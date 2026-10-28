package com.infimatrix.nova;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.infimatrix.nova.MockServer.Reply;
import com.infimatrix.nova.errors.NovaException;
import com.infimatrix.nova.errors.NovaServerException;
import com.infimatrix.nova.http.ApiRequest;
import com.infimatrix.nova.http.ApiResult;
import com.infimatrix.nova.http.HttpMethod;
import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;

/**
 * Tests added after mutation testing (PIT) showed that these behaviours were not pinned down. Expected values come
 * from docs/conventions.md and docs/error-handling.md (backoff {@code base * 2^attempt}, {@code Retry-After}, empty
 * bodies, error wire fields), not from reading the implementation.
 */
class RetryAndFormatTest {

    @Test
    void backoffDoublesWithEachRetry() {
        // docs: backoff = base * 2^attempt. Two retries with a 120 ms base sleep at least 120 + 240 = 360 ms in total.
        try (MockServer server = new MockServer()) {
            server.reply(Reply.error(503, "UNAVAILABLE", "down", "{}"));
            NovaClient client = server.clientBuilder().retryBackoff(Duration.ofMillis(120)).retryJitter(false)
                    .maxRetries(2).build();
            long start = System.nanoTime();
            assertThrows(NovaServerException.class, () -> client.templates().get("t-1"));
            long elapsedMs = (System.nanoTime() - start) / 1_000_000;
            assertEquals(3, server.requests().size());
            assertTrue(elapsedMs >= 355, "waited only " + elapsedMs + " ms");
            assertTrue(elapsedMs < 360 + 1500, "waited " + elapsedMs + " ms, far beyond 120 + 240");
        }
    }

    @Test
    void retryAfterIsHonouredBeforeTheNextAttempt() {
        // docs: Retry-After is honoured. A 1 s header must delay the retry by about a second.
        try (MockServer server = new MockServer()) {
            AtomicInteger calls = new AtomicInteger();
            server.reply(r -> calls.getAndIncrement() == 0
                    ? Reply.error(429, "RATE_LIMIT_EXCEEDED", "slow", "{}").withHeader("Retry-After", "1")
                    : Reply.ok("{\"id\":\"t-1\",\"name\":\"n\"}"));
            long start = System.nanoTime();
            assertEquals("t-1", server.clientBuilder().build().templates().get("t-1").id());
            long elapsedMs = (System.nanoTime() - start) / 1_000_000;
            assertEquals(2, server.requests().size());
            assertTrue(elapsedMs >= 950, "retried after only " + elapsedMs + " ms");
        }
    }

    @Test
    void emptyBodiesMeanNoData() {
        // docs: "204/empty bodies -> no data". Covers 204 and a 200 with a zero-length body.
        try (MockServer server = new MockServer()) {
            NovaClient client = server.clientBuilder().build();
            server.reply(Reply.noContent());
            assertNull(client.transport().send(ApiRequest.of(HttpMethod.GET, "x/")).data());
            server.reply(Reply.text(200, "application/json", ""));
            ApiResult empty = client.transport().send(ApiRequest.of(HttpMethod.GET, "x/"));
            assertNull(empty.data());
            assertTrue(empty.success());
        }
    }

    @Test
    void errorMessageCarriesStatusCodeAndCorrelationIdInThatOrder() {
        // docs: errors carry status, code and correlation id; Python and TypeScript format them as
        // "<message> (status=N, code=C, correlation_id=ID)".
        try (MockServer server = new MockServer()) {
            server.reply(Reply.error(404, "NOT_FOUND", "Nothing here", "{}"));
            NovaException e = assertThrows(NovaException.class, () -> server.clientBuilder().build().templates().get("t"));
            assertEquals("Nothing here (status=404, code=NOT_FOUND, correlation_id=corr-err)", e.getMessage());
            assertEquals(404, e.statusCode());
            assertEquals("NOT_FOUND", e.errorCode());
            assertEquals("corr-err", e.correlationId());
        }
        NovaException bare = new NovaException("plain");
        assertEquals("plain", bare.getMessage());
        assertNull(bare.statusCode());
    }

    @Test
    void configStringRedactsCredentialsByLength() {
        // docs: credentials are redacted in toString. Short secrets are fully hidden; longer ones keep only a prefix.
        String twelve = "abcdefghijkl";
        String thirteen = "abcdefghijklm";
        String shortForm = NovaClient.builder().apiKey(twelve).accessToken(thirteen).build().config().toString();
        assertFalse(shortForm.contains(twelve));
        assertFalse(shortForm.contains(thirteen));
        assertTrue(shortForm.contains("apiKey=[REDACTED]"), shortForm);
        assertTrue(shortForm.contains("accessToken=abcdefgh...[REDACTED]"), shortForm);
        assertTrue(NovaClient.builder().build().config().toString().contains("apiKey=<none>"));
    }

    @Test
    void paginationStopsAtTheLastPageEvenIfNextIsStillSet() {
        // Loop guard shared by all SDKs: a server that keeps sending a "next" link on the final page must not make
        // iteration run past total_pages (Python iter_pages / TypeScript getNextPage stop the same way).
        try (MockServer server = new MockServer()) {
            server.reply(r -> Reply.json(200, "{\"success\":true,\"pagination\":{\"count\":2,\"next\":\"http://x/?page=3\","
                    + "\"previous\":null,\"page\":2,\"total_pages\":2,\"page_size\":2},\"results\":[{\"id\":\"a\"},{\"id\":\"b\"}]}"));
            Page<?> page = server.clientBuilder().build().templates().list(Query.builder().page(2).build());
            assertTrue(page.hasNext());
            assertTrue(page.nextPage().isEmpty());
            assertEquals(1, server.requests().size());
        }
    }

    @Test
    void multiplePlaceholdersAreFilledInOrderAndEncoded() {
        try (MockServer server = new MockServer()) {
            server.clientBuilder().build().transport()
                    .send(ApiRequest.of(HttpMethod.GET, "tenants/{}/members/{}/", "a b", "c/d"));
            assertEquals("/api/v1/tenants/a%20b/members/c%2Fd/", server.last().path());
        }
    }

    @org.junit.jupiter.params.ParameterizedTest
    @org.junit.jupiter.params.provider.CsvSource(delimiter = '|', value = {
        "http://user:pw@host.example/p?q=1#f|http://host.example/p?q=1#f",
        "http://user:se@cret@host.example/next|http://host.example/next",
        "http://u:p%40ss@host.example:8443/x|http://host.example:8443/x",
        "http://:onlypw@host.example/|http://host.example/",
        "http://host.example/a@b|http://host.example/a@b",
    })
    void redirectLocationUserinfoEndsAtTheLastAtSign(String location, String reported) {
        // docs: credentials are stripped from the reported location; userinfo ends at the last '@' (RFC 3986 3.2).
        try (MockServer server = new MockServer()) {
            server.reply(new Reply(302, "text/plain", "", java.util.Map.of("Location", location), 0));
            NovaException e = assertThrows(NovaException.class, () -> server.clientBuilder().build().templates().get("t"));
            assertTrue(e.getMessage().contains("redirect to " + reported + "."), e.getMessage());
        }
    }
}
