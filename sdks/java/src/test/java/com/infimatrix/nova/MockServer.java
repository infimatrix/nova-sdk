package com.infimatrix.nova;

import com.sun.net.httpserver.Headers;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.Executors;
import java.util.function.Function;

/** A local HTTP server (JDK built-in) that records requests and answers with scripted responses. */
final class MockServer implements AutoCloseable {

    /** A recorded request. */
    record Recorded(String method, String path, String query, Map<String, String> headers, byte[] body) {
        String bodyText() {
            return new String(body, StandardCharsets.UTF_8);
        }

        String header(String name) {
            return headers.get(name.toLowerCase(Locale.ROOT));
        }
    }

    /** A scripted response. */
    record Reply(int status, String contentType, String body, Map<String, String> headers, long delayMillis) {
        static Reply json(int status, String body) {
            return new Reply(status, "application/json", body, Map.of(), 0);
        }

        static Reply ok(String dataJson) {
            return json(200, envelope(dataJson));
        }

        static Reply created(String dataJson) {
            return json(201, envelope(dataJson));
        }

        static Reply noContent() {
            return new Reply(204, null, "", Map.of(), 0);
        }

        static Reply text(int status, String contentType, String body) {
            return new Reply(status, contentType, body, Map.of(), 0);
        }

        static Reply error(int status, String code, String message, String detailsJson) {
            return json(status, "{\"success\":false,\"message\":\"" + message + "\",\"data\":null,\"error\":{\"code\":\""
                    + code + "\",\"message\":\"" + message + "\",\"details\":" + detailsJson + "},\"meta\":"
                    + "{\"correlation_id\":\"corr-err\"}}");
        }

        Reply withHeader(String name, String value) {
            Map<String, String> copy = new java.util.LinkedHashMap<>(headers);
            copy.put(name, value);
            return new Reply(status, contentType, body, copy, delayMillis);
        }

        Reply delayed(long millis) {
            return new Reply(status, contentType, body, headers, millis);
        }
    }

    static String envelope(String dataJson) {
        return "{\"success\":true,\"message\":\"Operation completed successfully.\",\"data\":" + dataJson
                + ",\"errors\":null,\"meta\":{\"timestamp\":\"2026-10-26T00:00:00Z\",\"correlation_id\":\"corr-1\"}}";
    }

    static String page(int number, int totalPages, String resultsJson) {
        String next = number < totalPages ? "\"http://x/?page=" + (number + 1) + "\"" : "null";
        return "{\"success\":true,\"pagination\":{\"count\":" + totalPages * 2 + ",\"next\":" + next
                + ",\"previous\":null,\"page\":" + number + ",\"total_pages\":" + totalPages + ",\"page_size\":2},"
                + "\"results\":" + resultsJson + "}";
    }

    private final HttpServer server;
    private final List<Recorded> requests = new CopyOnWriteArrayList<>();
    private volatile Function<Recorded, Reply> handler = r -> Reply.ok("{}");

    MockServer() {
        try {
            server = HttpServer.create(new InetSocketAddress(InetAddress.getLoopbackAddress(), 0), 0);
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }
        server.setExecutor(Executors.newCachedThreadPool());
        server.createContext("/", this::handle);
        server.start();
    }

    String url() {
        return "http://127.0.0.1:" + server.getAddress().getPort();
    }

    MockServer reply(Function<Recorded, Reply> fn) {
        this.handler = fn;
        return this;
    }

    MockServer reply(Reply fixed) {
        return reply(r -> fixed);
    }

    List<Recorded> requests() {
        return requests;
    }

    Recorded last() {
        return requests.get(requests.size() - 1);
    }

    private void handle(HttpExchange exchange) throws IOException {
        byte[] body = exchange.getRequestBody().readAllBytes();
        Map<String, String> headers = new java.util.LinkedHashMap<>();
        Headers in = exchange.getRequestHeaders();
        in.forEach((k, v) -> headers.put(k.toLowerCase(Locale.ROOT), String.join(",", v)));
        Recorded recorded = new Recorded(exchange.getRequestMethod(), exchange.getRequestURI().getRawPath(),
                exchange.getRequestURI().getRawQuery(), headers, body);
        requests.add(recorded);
        Reply reply = handler.apply(recorded);
        if (reply.delayMillis() > 0) {
            try {
                Thread.sleep(reply.delayMillis());
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
        reply.headers().forEach((k, v) -> exchange.getResponseHeaders().add(k, v));
        if (reply.contentType() != null) {
            exchange.getResponseHeaders().add("Content-Type", reply.contentType());
        }
        byte[] out = reply.body().getBytes(StandardCharsets.UTF_8);
        exchange.sendResponseHeaders(reply.status(), reply.status() == 204 ? -1 : out.length);
        if (reply.status() != 204) {
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(out);
            }
        }
        exchange.close();
    }

    NovaClient.Builder clientBuilder() {
        return NovaClient.builder().baseUrl(url()).apiKey("nova_key_test_secret_1234567890")
                .retryBackoff(java.time.Duration.ofMillis(1)).retryJitter(false);
    }

    @Override
    public void close() {
        server.stop(0);
    }
}
