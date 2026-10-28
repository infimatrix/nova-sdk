package com.infimatrix.nova;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.infimatrix.nova.MockServer.Reply;
import com.infimatrix.nova.errors.NovaClientValidationException;
import com.infimatrix.nova.errors.NovaException;
import com.infimatrix.nova.models.Template;
import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import net.jqwik.api.Arbitraries;
import net.jqwik.api.Arbitrary;
import net.jqwik.api.ForAll;
import net.jqwik.api.Property;
import net.jqwik.api.Provide;
import net.jqwik.api.constraints.AlphaChars;
import net.jqwik.api.constraints.IntRange;
import net.jqwik.api.constraints.NumericChars;
import net.jqwik.api.constraints.Size;
import net.jqwik.api.constraints.StringLength;

/**
 * Property tests for invariants the documentation states (docs/conventions.md, authentication.md). Every property
 * cites its source and asserts nothing the docs do not promise. jqwik prints the seed of a failing try; replay it with
 * {@code -Djqwik.seeds.whenfixed=...} or the seed shown in the report.
 */
class PropertyTest {
    private static final String PREFIX = "/api/v1/templates/";

    /** conventions.md "Path ids": a hostile id cannot add path segments or query strings. */
    @Property(tries = 150)
    void pathIdNeverAddsSegmentsOrQuery(@ForAll @StringLength(max = 40) String id) {
        try (MockServer server = new MockServer()) {
            server.reply(Reply.ok("{\"id\":\"x\",\"name\":\"n\"}"));
            NovaClient client = server.clientBuilder().build();
            String stripped = id.strip();
            if (stripped.isEmpty() || stripped.equals(".") || stripped.equals("..")) {
                assertThrows(NovaClientValidationException.class, () -> client.templates().get(id));
                assertEquals(0, server.requests().size());
                return;
            }
            client.templates().get(id);
            assertEquals(1, server.requests().size());
            String raw = server.last().path();
            assertEquals(null, server.last().query());
            assertTrue(raw.startsWith(PREFIX) && raw.endsWith("/"), raw);
            String segment = raw.substring(PREFIX.length(), raw.length() - 1);
            assertFalse(segment.contains("/"), raw);
            assertFalse(segment.equals(".") || segment.equals(".."), raw);
            String decoded = URI.create("http://h" + PREFIX + segment + "/").getPath();
            assertEquals(stripped, decoded.substring(PREFIX.length(), decoded.length() - 1));
        }
    }

    /** RFC 3986 / form encoding: the server decodes exactly the value the caller passed. */
    @Property(tries = 150)
    void searchValueRoundTrips(@ForAll @StringLength(min = 1, max = 40) String value) {
        net.jqwik.api.Assume.that(value.strip().equals(value));
        try (MockServer server = new MockServer()) {
            server.reply(Reply.json(200, MockServer.page(1, 1, "[]")));
            server.clientBuilder().build().templates().list(Query.builder().search(value).build());
            List<String> sent = new ArrayList<>();
            for (String pair : server.last().query().split("&")) {
                String[] kv = pair.split("=", 2);
                if (URLDecoder.decode(kv[0], StandardCharsets.UTF_8).equals("search")) {
                    sent.add(URLDecoder.decode(kv[1], StandardCharsets.UTF_8));
                }
            }
            assertEquals(List.of(value), sent);
        }
    }

    /** conventions.md "Base URL": strip trailing '/', '/api' or '/api/v1'; result is stable. */
    @Property(tries = 100)
    void baseUrlNormalisation(
            @ForAll @AlphaChars @StringLength(min = 1, max = 10) String host,
            @ForAll("suffixes") String suffix,
            @ForAll @IntRange(min = 1, max = 65535) int port) {
        String origin = "http://" + host.toLowerCase() + ":" + port;
        String once = NovaClient.builder().baseUrl(origin + suffix).apiKey("k").build().config().baseUrl();
        assertEquals(origin, once);
        assertEquals(once, NovaClient.builder().baseUrl(once).apiKey("k").build().config().baseUrl());
    }

    @Provide
    Arbitrary<String> suffixes() {
        return Arbitraries.of("", "/", "/api", "/api/", "/api/v1", "/api/v1/");
    }

    /** authentication.md "Handling secrets": credentials never appear in messages or string forms. */
    @Property(tries = 100)
    void apiKeyNeverAppearsInErrorsOrStrings(
            @ForAll @AlphaChars @NumericChars @StringLength(min = 8, max = 40) String key,
            @ForAll("statuses") int status) {
        String secret = "nova_key_" + key;
        try (MockServer server = new MockServer()) {
            server.reply(Reply.error(status, "X", "failure", "{}"));
            NovaClient client = server.clientBuilder().apiKey(secret).maxRetries(0).build();
            NovaException e = assertThrows(NovaException.class,
                    () -> client.templates().create(com.infimatrix.nova.models.TemplateRequest.builder().name("n").build()));
            for (String text : new String[] {e.toString(), String.valueOf(e.getMessage()), client.toString(),
                    client.config().toString()}) {
                assertFalse(text.contains(secret), text);
            }
        }
    }

    @Provide
    Arbitrary<Integer> statuses() {
        return Arbitraries.of(400, 401, 403, 404, 409, 418, 429, 500, 502, 503);
    }

    /** conventions.md "Pagination": iteration visits every item once, in order. */
    @Property(tries = 60)
    void iterationVisitsEveryItemOnceInOrder(@ForAll @Size(min = 1, max = 6) List<@IntRange(min = 0, max = 5) Integer> sizes) {
        List<List<String>> pages = new ArrayList<>();
        int n = 0;
        for (int size : sizes) {
            List<String> ids = new ArrayList<>();
            for (int i = 0; i < size; i++) {
                ids.add("id-" + n++);
            }
            pages.add(ids);
        }
        List<Integer> requested = new ArrayList<>();
        try (MockServer server = new MockServer()) {
            server.reply(r -> {
                int page = 1;
                if (r.query() != null) {
                    for (String pair : r.query().split("&")) {
                        if (pair.startsWith("page=")) {
                            page = Integer.parseInt(pair.substring(5));
                        }
                    }
                }
                requested.add(page);
                StringBuilder results = new StringBuilder("[");
                for (String id : pages.get(page - 1)) {
                    results.append(results.length() > 1 ? "," : "").append("{\"id\":\"").append(id).append("\",\"name\":\"n\"}");
                }
                return Reply.json(200, MockServer.page(page, pages.size(), results.append(']').toString()));
            });
            List<String> seen = new ArrayList<>();
            for (Template t : server.clientBuilder().build().templates().list(Query.builder().pageSize(10).build())) {
                seen.add(t.id());
            }
            List<String> expected = new ArrayList<>();
            pages.forEach(expected::addAll);
            assertEquals(expected, seen);
            List<Integer> expectedPages = new ArrayList<>();
            for (int i = 1; i <= pages.size(); i++) {
                expectedPages.add(i);
            }
            assertEquals(expectedPages, requested);
        }
    }
}
