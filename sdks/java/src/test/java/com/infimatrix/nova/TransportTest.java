package com.infimatrix.nova;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.infimatrix.nova.MockServer.Reply;
import com.infimatrix.nova.errors.NovaApiException;
import com.infimatrix.nova.errors.NovaAbortedException;
import com.infimatrix.nova.errors.NovaAuthenticationException;
import com.infimatrix.nova.errors.NovaClientValidationException;
import com.infimatrix.nova.errors.NovaConnectionException;
import com.infimatrix.nova.errors.NovaException;
import com.infimatrix.nova.errors.NovaNotFoundException;
import com.infimatrix.nova.errors.NovaPermissionException;
import com.infimatrix.nova.errors.NovaRateLimitException;
import com.infimatrix.nova.errors.NovaRedirectException;
import com.infimatrix.nova.errors.NovaServerException;
import com.infimatrix.nova.errors.NovaTimeoutException;
import com.infimatrix.nova.errors.NovaValidationException;
import com.infimatrix.nova.http.ApiRequest;
import com.infimatrix.nova.http.ApiResult;
import com.infimatrix.nova.http.HttpMethod;
import com.infimatrix.nova.models.Tenant;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

class TransportTest {
    private static final String TENANT = "11111111-1111-1111-1111-111111111111";

    private static ApiRequest get(String template, Object... args) {
        return ApiRequest.of(HttpMethod.GET, template, args);
    }

    @Test
    void sendsAuthTenantCorrelationAndUserAgentHeaders() {
        try (MockServer server = new MockServer()) {
            NovaClient client = server.clientBuilder().tenantId(TENANT).defaultHeader("X-Custom", "yes").build()
                    .with(RequestOptions.builder().correlationId(" abc ").header("X-Per-Call", "1").build());
            client.transport().send(get("health/"));
            MockServer.Recorded r = server.last();
            assertEquals("Bearer nova_key_test_secret_1234567890", r.header("authorization"));
            assertEquals(TENANT, r.header("x-tenant-id"));
            assertEquals("abc", r.header("x-correlation-id"));
            assertEquals("application/json", r.header("accept"));
            assertEquals("yes", r.header("x-custom"));
            assertEquals("1", r.header("x-per-call"));
            assertEquals("Nova-Java-SDK/" + Version.VERSION, r.header("user-agent"));
            assertEquals("/api/v1/health/", r.path());
        }
    }

    @Test
    void perCallTenantOverridesAndIsValidated() {
        try (MockServer server = new MockServer()) {
            NovaClient client = server.clientBuilder().tenantId(TENANT).build();
            String other = "22222222-2222-2222-2222-222222222222";
            client.withTenant(other).health();
            assertEquals(other, server.last().header("x-tenant-id"));
            client.with(RequestOptions.builder().tenantId(other).build()).health();
            assertEquals(other, server.last().header("x-tenant-id"));
            NovaClient bad = client.with(RequestOptions.builder().tenantId("bad").build());
            assertThrows(NovaClientValidationException.class, bad::health);
        }
    }

    @Test
    void unwrapsEnvelopeAndKeepsCorrelationId() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.ok("{\"a\":1}"));
            ApiResult result = server.clientBuilder().build().transport().send(get("x/"));
            assertEquals(1, result.data().get("a").asInt());
            assertTrue(result.success());
            assertEquals("corr-1", result.correlationId());
        }
    }

    @Test
    void handlesEmptyCsvPlainAndUnenvelopedBodies() {
        try (MockServer server = new MockServer()) {
            NovaClient client = server.clientBuilder().build();
            server.reply(Reply.noContent());
            assertNull(client.transport().send(ApiRequest.of(HttpMethod.DELETE, "x/")).data());
            server.reply(Reply.text(200, "application/json", ""));
            assertNull(client.transport().send(get("x/")).data());
            server.reply(Reply.text(200, "text/csv", "a,b\n1,2\n"));
            assertEquals("a,b\n1,2\n", client.transport().sendText(get("x/")));
            server.reply(Reply.text(200, "text/plain", "plain text"));
            assertEquals("plain text", client.transport().sendText(get("x/")));
            server.reply(Reply.text(200, "application/json", "[1,2]"));
            assertEquals(2, client.transport().send(get("x/")).data().size());
            server.reply(Reply.ok("null"));
            assertEquals(java.util.List.of(), client.transport().sendList(get("x/"), Tenant.class));
            server.reply(Reply.text(200, "application/json", "[1,2]"));
            assertThrows(NovaException.class, () -> client.transport().sendList(get("x/"), Tenant.class));
        }
    }

    @Test
    void parsesTypedModelsIgnoringUnknownFields() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.ok("{\"id\":\"t1\",\"name\":\"Acme\",\"is_active\":true,\"future_field\":{\"x\":1}}"));
            Tenant tenant = server.clientBuilder().tenantId(TENANT).build().tenants().get(null);
            assertEquals("Acme", tenant.name());
            assertTrue(tenant.isActive());
            assertEquals("/api/v1/tenants/" + TENANT + "/", server.last().path());
        }
    }

    @Test
    void mismatchedResponseShapeBecomesNovaException() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.ok("{\"id\":{\"unexpected\":\"object\"}}"));
            NovaException e = assertThrows(NovaException.class,
                    () -> server.clientBuilder().tenantId(TENANT).build().tenants().get(null));
            assertEquals("INVALID_RESPONSE", e.errorCode());
        }
    }

    @ParameterizedTest
    @CsvSource({"400,NovaValidationException", "401,NovaAuthenticationException", "403,NovaPermissionException",
        "404,NovaNotFoundException", "429,NovaRateLimitException", "500,NovaServerException", "503,NovaServerException",
        "418,NovaApiException"})
    void mapsStatusesToTypedExceptions(int status, String type) {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.error(status, "CODE_X", "boom", "{\"f\":[\"bad\"]}"));
            NovaApiException e = assertThrows(NovaApiException.class,
                    () -> ApiCall.post(server.clientBuilder().maxRetries(0).build()));
            assertEquals(type, e.getClass().getSimpleName());
            assertEquals(status, e.statusCode());
            assertEquals("CODE_X", e.errorCode());
            assertEquals("corr-err", e.correlationId());
            assertEquals(Map.of("f", java.util.List.of("bad")), e.details());
            assertTrue(e.getMessage().contains("boom") && e.getMessage().contains("status=" + status));
            assertFalse(e.getMessage().contains("nova_key_test"));
        }
    }

    @Test
    void usesDefaultCodeWhenServerOmitsOne() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.text(404, "application/json", "{}"));
            NovaNotFoundException e = assertThrows(NovaNotFoundException.class,
                    () -> server.clientBuilder().build().transport().send(get("x/")));
            assertEquals("API_ERROR", e.errorCode());
        }
    }

    @ParameterizedTest
    @CsvSource(delimiter = '|', value = {
        "400|{\"error\": \"Tenant context required.\"}|Tenant context required.",
        "403|{\"detail\": \"No tenant context.\"}|No tenant context.",
        "400|{\"message\": \"Nope\"}|Nope",
        "502|<html><head><title> Bad Gateway </title></head></html>|HTTP 502 Error: Bad Gateway",
        "500||HTTP 500 Error",
    })
    void parsesLegacyAndNonJsonErrorBodies(int status, String body, String expected) {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.text(status, "text/plain", body == null ? "" : body));
            NovaApiException e = assertThrows(NovaApiException.class,
                    () -> server.clientBuilder().maxRetries(0).build().transport().send(get("x/")));
            assertEquals(expected, e.rawMessage());
        }
    }

    @Test
    void parsesArrayAndFieldMapErrors() {
        try (MockServer server = new MockServer()) {
            NovaClient client = server.clientBuilder().build();
            server.reply(Reply.text(400, "application/json", "[\"bad\"]"));
            NovaValidationException array = assertThrows(NovaValidationException.class, () -> ApiCall.post(client));
            assertEquals(Map.of("errors", java.util.List.of("bad")), array.details());
            server.reply(Reply.text(400, "application/json", "{\"name\":[\"required\"]}"));
            NovaValidationException drf = assertThrows(NovaValidationException.class, () -> ApiCall.post(client));
            assertEquals(Map.of("name", java.util.List.of("required")), drf.details());
        }
    }

    @Test
    void rateLimitExposesRetryAfter() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.error(429, "RATE_LIMIT_EXCEEDED", "slow", "{}").withHeader("Retry-After", "7"));
            NovaRateLimitException e = assertThrows(NovaRateLimitException.class,
                    () -> server.clientBuilder().maxRetries(0).build().transport().send(get("x/")));
            assertEquals(Duration.ofSeconds(7), e.retryAfter());
        }
    }

    @Test
    void retriesIdempotentRequestsOnTransientStatuses() {
        try (MockServer server = new MockServer()) {
            AtomicInteger n = new AtomicInteger();
            server.reply(r -> n.incrementAndGet() < 3 ? Reply.error(503, "DOWN", "down", "{}") : Reply.ok("{\"ok\":1}"));
            ApiResult result = server.clientBuilder().maxRetries(3).build().transport().send(get("x/"));
            assertEquals(1, result.data().get("ok").asInt());
            assertEquals(3, server.requests().size());
        }
    }

    @Test
    void stopsAfterMaxRetries() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.error(503, "DOWN", "down", "{}"));
            assertThrows(NovaServerException.class, () -> server.clientBuilder().maxRetries(2).build().transport().send(get("x/")));
            assertEquals(3, server.requests().size());
        }
    }

    @ParameterizedTest
    @CsvSource({"POST", "PUT", "PATCH", "DELETE"})
    void neverRetriesUnsafeMethods(String method) {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.error(503, "DOWN", "down", "{}"));
            NovaClient client = server.clientBuilder().maxRetries(3).build();
            assertThrows(NovaServerException.class,
                    () -> client.transport().send(ApiRequest.of(HttpMethod.valueOf(method), "x/")));
            assertEquals(1, server.requests().size());
        }
    }

    @Test
    void retriesUnsafeMethodsOnlyWhenExplicitlyAllowed() {
        try (MockServer server = new MockServer()) {
            AtomicInteger n = new AtomicInteger();
            server.reply(r -> n.incrementAndGet() < 2 ? Reply.error(502, "BAD", "bad", "{}") : Reply.ok("{}"));
            server.clientBuilder().maxRetries(2).build().transport()
                    .send(ApiRequest.of(HttpMethod.POST, "x/").allowRetry(true));
            assertEquals(2, server.requests().size());
        }
    }

    @Test
    void doesNotRetryNonTransientStatuses() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.error(404, "NF", "gone", "{}"));
            assertThrows(NovaNotFoundException.class, () -> server.clientBuilder().maxRetries(3).build().transport().send(get("x/")));
            assertEquals(1, server.requests().size());
        }
    }

    @Test
    void honoursRetryAfterInsteadOfBackoff() {
        try (MockServer server = new MockServer()) {
            AtomicInteger n = new AtomicInteger();
            server.reply(r -> n.incrementAndGet() < 2
                    ? Reply.error(429, "RL", "slow", "{}").withHeader("Retry-After", "0.2") : Reply.ok("{}"));
            long start = System.nanoTime();
            server.clientBuilder().maxRetries(1).retryBackoff(Duration.ofSeconds(30)).build().transport().send(get("x/"));
            long elapsedMs = (System.nanoTime() - start) / 1_000_000;
            assertTrue(elapsedMs >= 190 && elapsedMs < 5000, "elapsed " + elapsedMs);
        }
    }

    @Test
    void redirectsAreNeverFollowedAndCredentialsAreStripped() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.text(302, "text/plain", "").withHeader("Location", "https://user:pw@evil.example/x"));
            NovaRedirectException e = assertThrows(NovaRedirectException.class,
                    () -> server.clientBuilder().build().transport().send(get("x/")));
            assertEquals("https://evil.example/x", e.location());
            assertFalse(e.getMessage().contains("pw"));
            assertEquals(1, server.requests().size());
        }
    }

    @Test
    void requestTimeoutRaisesNovaTimeoutException() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.ok("{}").delayed(1500));
            assertThrows(NovaTimeoutException.class, () -> server.clientBuilder().maxRetries(0)
                    .requestTimeout(Duration.ofMillis(200)).build().transport().send(get("x/")));
        }
    }

    @Test
    void perCallTimeoutOverridesTheDefault() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.ok("{}").delayed(1500));
            NovaClient client = server.clientBuilder().maxRetries(0).build()
                    .with(RequestOptions.builder().timeout(Duration.ofMillis(200)).build());
            assertThrows(NovaTimeoutException.class, () -> client.transport().send(get("x/")));
        }
    }

    @Test
    void connectionFailureRaisesNovaConnectionException() {
        NovaClient client = NovaClient.builder().baseUrl("http://127.0.0.1:1").apiKey("k").maxRetries(1)
                .retryBackoff(Duration.ofMillis(1)).build();
        NovaConnectionException e = assertThrows(NovaConnectionException.class, client::health);
        assertEquals("CONNECTION_ERROR", e.errorCode());
    }

    @Test
    void interruptedThreadRaisesAbortedAndKeepsInterruptFlag() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.ok("{}").delayed(1000));
            NovaClient client = server.clientBuilder().build();
            Thread.currentThread().interrupt();
            try {
                assertThrows(NovaAbortedException.class, client::health);
                assertTrue(Thread.currentThread().isInterrupted());
            } finally {
                Thread.interrupted();
            }
        }
    }

    @Test
    void pathIdentifiersAreEncodedAndValidated() {
        try (MockServer server = new MockServer()) {
            NovaClient client = server.clientBuilder().build();
            client.templates().get("a/../b?x=1#f");
            assertEquals("/api/v1/templates/a%2F..%2Fb%3Fx%3D1%23f/", server.last().path());
            assertNull(server.last().query());
            client.templates().get("ünï cödé");
            assertTrue(server.last().path().contains("%C3%BCn%C3%AF%20c%C3%B6d%C3%A9"));
            assertThrows(NovaClientValidationException.class, () -> client.templates().get("  "));
            assertThrows(NovaClientValidationException.class, () -> client.templates().get(null));
            assertEquals(2, server.requests().size());
        }
    }

    @Test
    void queryParametersAreEncodedAndRepeated() {
        try (MockServer server = new MockServer()) {
            server.clientBuilder().build().templates().list(
                    Query.builder().search("a b&c").page(2).param("ids", java.util.List.of(1, 2)).param("skip", null).build());
            assertEquals("search=a+b%26c&page=2&ids=1&ids=2", server.last().query());
        }
    }

    @Test
    void secretsNeverAppearInExceptionsOrToString() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.error(401, "NOT_AUTHENTICATED", "bad credentials", "{}"));
            NovaClient client = server.clientBuilder().build();
            NovaAuthenticationException e = assertThrows(NovaAuthenticationException.class, client::health);
            assertFalse(e.toString().contains("nova_key_test_secret"));
            assertFalse(client.toString().contains("nova_key_test_secret"));
            assertInstanceOf(NovaApiException.class, e);
        }
    }

    @Test
    void permissionDeniedMapsTo403() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.error(403, "DENIED", "no", "{}"));
            assertThrows(NovaPermissionException.class, () -> server.clientBuilder().build().health());
        }
    }

    /** Helper issuing a POST through the public transport. */
    private static final class ApiCall {
        static void post(NovaClient client) {
            client.transport().send(ApiRequest.of(HttpMethod.POST, "x/"));
        }
    }
}
