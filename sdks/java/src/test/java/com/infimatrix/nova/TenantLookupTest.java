package com.infimatrix.nova;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.infimatrix.nova.MockServer.Reply;
import com.infimatrix.nova.errors.NovaClientValidationException;
import com.infimatrix.nova.models.TemplateRenderResult;
import com.infimatrix.nova.models.WebhookEndpointCreateUpdate;
import com.infimatrix.nova.models.WebhookEndpointCreateUpdateRequest;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;

/**
 * An application that only knows the server URL and an API key must be able to call tenant-scoped operations: when no
 * tenant is named (argument, per-call options, client default) the SDK asks the server which tenant the credentials
 * resolve to ({@code GET auth/me/}). Tenant deletion is never inferred. Also pins the corrected response types.
 */
class TenantLookupTest {
    private static final String TENANT = "11111111-1111-1111-1111-111111111111";
    private static final String OTHER = "22222222-2222-2222-2222-222222222222";

    private static java.util.function.Function<MockServer.Recorded, Reply> me(String currentTenantJson) {
        return r -> r.path().equals("/api/v1/auth/me/")
                ? Reply.ok("{\"email\":\"a@b.co\",\"current_tenant\":" + currentTenantJson + "}")
                : r.path().endsWith("/members/")
                        ? Reply.json(200, MockServer.page(1, 1, "[]"))
                        : Reply.ok("{\"id\":\"" + TENANT + "\",\"name\":\"Acme\"}");
    }

    @Test
    void looksTheTenantUpOnceAndUsesItInThePathWhenNoneIsConfigured() {
        try (MockServer server = new MockServer()) {
            server.reply(me("{\"id\":\"" + TENANT + "\",\"name\":\"Acme\"}"));
            NovaClient client = server.clientBuilder().build();
            client.tenants().memberships().list(null, Query.empty());
            assertEquals(List.of("/api/v1/auth/me/", "/api/v1/tenants/" + TENANT + "/members/"),
                    server.requests().stream().map(MockServer.Recorded::path).toList());
            assertEquals("Acme", client.tenants().get(null).name());
            assertEquals("/api/v1/tenants/" + TENANT + "/", server.last().path());
        }
    }

    @Test
    void configuredTenantAndExplicitIdsNeverTriggerALookup() {
        try (MockServer server = new MockServer()) {
            server.reply(me("{\"id\":\"" + OTHER + "\"}"));
            NovaClient client = server.clientBuilder().tenantId(TENANT).build();
            assertEquals(TENANT, client.tenants().currentTenantId());
            client.tenants().memberships().list(null, Query.empty());
            client.tenants().memberships().list(OTHER, Query.empty());
            assertEquals(List.of("/api/v1/tenants/" + TENANT + "/members/", "/api/v1/tenants/" + OTHER + "/members/"),
                    server.requests().stream().map(MockServer.Recorded::path).toList());
        }
    }

    @ParameterizedTest
    @ValueSource(strings = {"null", "{}", "{\"id\":\"\"}"})
    void failsClearlyWhenTheServerReportsNoTenant(String current) {
        try (MockServer server = new MockServer()) {
            server.reply(me(current));
            NovaClientValidationException e = assertThrows(NovaClientValidationException.class,
                    () -> server.clientBuilder().build().tenants().memberships().list(null, Query.empty()));
            assertTrue(e.getMessage().contains("did not report a current tenant"), e.getMessage());
        }
    }

    @Test
    void theIdTheServerReportsIsValidatedBeforeItIsUsed() {
        try (MockServer server = new MockServer()) {
            server.reply(me("{\"id\":\"../../etc\"}"));
            assertThrows(NovaClientValidationException.class,
                    () -> server.clientBuilder().build().tenants().memberships().list(null, Query.empty()));
            assertEquals(List.of("/api/v1/auth/me/"), server.requests().stream().map(MockServer.Recorded::path).toList());
        }
    }

    @Test
    void deletingATenantNeverInfersTheId() {
        try (MockServer server = new MockServer()) {
            server.reply(me("{\"id\":\"" + TENANT + "\"}"));
            assertThrows(NovaClientValidationException.class, () -> server.clientBuilder().build().tenants().delete(null));
            assertEquals(0, server.requests().size(), "not even a lookup request");
        }
    }

    @Test
    void templateRenderExposesSubjectAndHtmlContent() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.ok("{\"subject\":\"Hi Ada\",\"html_content\":\"<p>Hi Ada</p>\"}"));
            TemplateRenderResult result = server.clientBuilder().build().templates().render(TENANT, Map.of("name", "Ada"));
            assertEquals("Hi Ada", result.subject());
            assertEquals("<p>Hi Ada</p>", result.htmlContent());
        }
    }

    @Test
    void webhookCreationExposesTheSigningSecret() {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.json(201, MockServer.envelope("{\"id\":\"" + TENANT + "\",\"name\":\"w\",\"url\":\"https://x.test/h\","
                    + "\"secret\":\"whsec_abc\",\"secret_masked\":\"whsec_***\",\"created_at\":\"2026-11-02T00:00:00Z\"}")));
            WebhookEndpointCreateUpdate created = server.clientBuilder().build().webhooks()
                    .create(WebhookEndpointCreateUpdateRequest.builder().name("w").url("https://x.test/h").build());
            assertEquals("whsec_abc", created.secret());
            assertEquals("whsec_***", created.secretMasked());
            assertNotNull(created.createdAt());
        }
    }
}
