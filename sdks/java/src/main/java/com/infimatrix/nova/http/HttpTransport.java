package com.infimatrix.nova.http;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.NullNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;
import com.infimatrix.nova.NovaConfig;
import com.infimatrix.nova.Page;
import com.infimatrix.nova.Pagination;
import com.infimatrix.nova.Query;
import com.infimatrix.nova.RequestOptions;
import com.infimatrix.nova.Version;
import com.infimatrix.nova.errors.ApiErrors;
import com.infimatrix.nova.errors.NovaAbortedException;
import com.infimatrix.nova.errors.NovaClientValidationException;
import com.infimatrix.nova.errors.NovaConnectionException;
import com.infimatrix.nova.errors.NovaException;
import com.infimatrix.nova.errors.NovaTimeoutException;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpConnectTimeoutException;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpTimeoutException;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.concurrent.ThreadLocalRandom;

/**
 * Executes {@link ApiRequest}s: authentication, tenancy, timeouts, bounded retries of idempotent calls,
 * envelope unwrapping and typed errors.
 *
 * <p>Instances are immutable and thread-safe (the underlying {@link HttpClient} is). Use
 * {@link #with(NovaConfig, RequestOptions)} for per-call overrides. Nothing sensitive is logged.
 */
public final class HttpTransport {
    private static final System.Logger LOG = System.getLogger("com.infimatrix.nova.http");
    private static final Set<Integer> RETRYABLE = Set.of(429, 502, 503, 504);
    private static final Set<String> KNOWN_EXTENSIONS = Set.of(
            ".csv", ".gif", ".gz", ".htm", ".html", ".jpeg", ".jpg", ".json", ".pdf", ".png", ".svg", ".tar", ".txt",
            ".webp", ".xml", ".yaml", ".yml", ".zip");
    private static final Set<String> SKIPPED_ERROR_KEYS = Set.of("success", "message", "error", "errors", "meta", "data");
    private static final Duration MAX_RETRY_AFTER = Duration.ofSeconds(30);

    private final NovaConfig config;
    private final HttpClient client;
    private final RequestOptions options;
    private final ObjectMapper mapper = Json.mapper();

    /** Creates a transport. Normally obtained from {@code NovaClient}. */
    public HttpTransport(NovaConfig config, HttpClient client, RequestOptions options) {
        this.config = config;
        this.client = client;
        this.options = options == null ? RequestOptions.none() : options;
    }

    /** The configuration in effect. */
    public NovaConfig config() {
        return config;
    }

    /** The call options in effect. */
    public RequestOptions options() {
        return options;
    }

    /** Returns a transport sharing the HTTP client but using {@code newConfig} and {@code newOptions}. */
    public HttpTransport with(NovaConfig newConfig, RequestOptions newOptions) {
        return new HttpTransport(newConfig, client, newOptions);
    }

    // -- public API ---------------------------------------------------------------------------

    /** Sends a request and returns the unwrapped envelope. */
    public ApiResult send(ApiRequest request) {
        return parseSuccess(execute(request));
    }

    /** Sends a request and converts {@code data} to {@code type} ({@code null} when the body is empty). */
    public <T> T send(ApiRequest request, Class<T> type) {
        return convert(send(request).data(), mapper.constructType(type));
    }

    /** Sends a request and converts {@code data} to a list of {@code type} (empty unless the payload is an array). */
    public <T> List<T> sendList(ApiRequest request, Class<T> type) {
        JsonNode data = send(request).data();
        if (data == null || !data.isArray()) {
            return List.of(); // like the Python and TypeScript SDKs: anything but an array is an empty list
        }
        List<T> list = convert(data, mapper.getTypeFactory().constructCollectionType(List.class, type));
        return list == null ? List.of() : list;
    }

    /** Sends a request and returns the response body as text (CSV exports, sample templates). */
    public String sendText(ApiRequest request) {
        JsonNode data = send(request).data();
        return data == null || data.isNull() ? "" : data.isTextual() ? data.asText() : data.toString();
    }

    /** Sends a request and returns the raw 2xx response bytes. */
    public byte[] sendBytes(ApiRequest request) {
        return execute(request).body();
    }

    /** Fetches a paginated list endpoint ({@code GET}) as an auto-paginating {@link Page}. */
    public <T> Page<T> listPage(String template, Query query, Class<T> type, Object... pathArgs) {
        Query effective = query == null ? Query.empty() : query;
        ApiRequest request = ApiRequest.of(HttpMethod.GET, template, pathArgs).query(effective);
        return fetchPage(request, type, effective, template, pathArgs);
    }

    // -- paging -------------------------------------------------------------------------------

    private <T> Page<T> fetchPage(ApiRequest request, Class<T> type, Query query, String template, Object[] pathArgs) {
        ApiResult result = send(request);
        JsonNode data = result.data();
        java.util.function.IntFunction<Page<T>> next = number -> {
            Query nextQuery = query.toBuilder().page(number).build();
            ApiRequest nextRequest = ApiRequest.of(HttpMethod.GET, template, pathArgs).query(nextQuery);
            return fetchPage(nextRequest, type, nextQuery, template, pathArgs);
        };
        if (data != null && data.isObject() && data.has("results")) {
            List<T> items = convert(data.get("results"), mapper.getTypeFactory().constructCollectionType(List.class, type));
            Pagination pagination = data.has("pagination") && !data.get("pagination").isNull()
                    ? convert(data.get("pagination"), mapper.constructType(Pagination.class))
                    : Pagination.single(items == null ? 0 : items.size());
            return new Page<>(items == null ? List.of() : items, pagination, next);
        }
        if (data != null && data.isArray()) {
            List<T> items = convert(data, mapper.getTypeFactory().constructCollectionType(List.class, type));
            return new Page<>(items, Pagination.single(items.size()), null);
        }
        return new Page<>(List.of(), Pagination.single(0), null);
    }

    private <T> T convert(JsonNode node, com.fasterxml.jackson.databind.JavaType type) {
        if (node == null || node.isNull()) {
            return null;
        }
        try {
            return mapper.readerFor(type).readValue(node);
        } catch (IOException e) {
            throw new NovaException("Unexpected response shape: " + e.getMessage().lines().findFirst().orElse(""),
                    null, "INVALID_RESPONSE", null, null, e);
        }
    }

    // -- request building ---------------------------------------------------------------------

    /** Builds the absolute URL for an already-filled endpoint path. */
    String buildUrl(ApiRequest request) {
        String path = fillTemplate(request.template(), request.pathArgs());
        path = path.strip().replaceAll("^/+", "");
        if (path.equals("api/v1")) {
            path = "";
        } else if (path.startsWith("api/v1/")) {
            path = path.substring("api/v1/".length()).replaceAll("^/+", "");
        }
        if (!path.isEmpty() && !path.endsWith("/")) {
            String last = path.substring(path.lastIndexOf('/') + 1);
            int dot = last.lastIndexOf('.');
            String ext = dot >= 0 ? last.substring(dot).toLowerCase(Locale.ROOT) : "";
            if (!KNOWN_EXTENSIONS.contains(ext)) {
                path += "/";
            }
        }
        StringBuilder url = new StringBuilder(config.baseUrl()).append("/api/v1/").append(path);
        StringBuilder qs = new StringBuilder();
        request.query().params().forEach((name, values) -> {
            for (String value : values) {
                qs.append(qs.length() == 0 ? "" : "&").append(formEncode(name)).append('=').append(formEncode(value));
            }
        });
        return qs.length() == 0 ? url.toString() : url.append('?').append(qs).toString();
    }

    private static String fillTemplate(String template, List<String> args) {
        StringBuilder out = new StringBuilder();
        int next = 0;
        int i = 0;
        while (i < template.length()) {
            if (template.startsWith("{}", i)) {
                if (next >= args.size()) {
                    throw new NovaClientValidationException("Missing path argument for " + template);
                }
                out.append(encodeSegment(args.get(next++)));
                i += 2;
            } else {
                out.append(template.charAt(i++));
            }
        }
        return out.toString();
    }

    /** Validates and percent-encodes one path segment so it can never alter the request path. */
    static String encodeSegment(String value) {
        if (value == null || value.isBlank()) {
            throw new NovaClientValidationException("path identifiers must be non-empty strings.");
        }
        String stripped = value.strip();
        if (stripped.equals(".") || stripped.equals("..")) {
            // Dot-segments are normalised away by servers and intermediaries and would address another endpoint.
            throw new NovaClientValidationException("path identifiers must not be '.' or '..'.");
        }
        byte[] bytes = stripped.getBytes(StandardCharsets.UTF_8);
        StringBuilder out = new StringBuilder();
        for (byte b : bytes) {
            int c = b & 0xff;
            if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')
                    || c == '-' || c == '.' || c == '_' || c == '~') {
                out.append((char) c);
            } else {
                out.append('%').append(String.format("%02X", c));
            }
        }
        return out.toString();
    }

    private static String formEncode(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }

    private HttpRequest buildRequest(ApiRequest request, String url, Map<String, String> headers) {
        HttpRequest.BodyPublisher body = HttpRequest.BodyPublishers.noBody();
        String contentType = null;
        try {
            if (request.json() != null) {
                body = HttpRequest.BodyPublishers.ofByteArray(mapper.writeValueAsBytes(request.json()));
                contentType = "application/json";
            } else if (request.isMultipart()) {
                String boundary = "nova-" + UUID.randomUUID();
                body = HttpRequest.BodyPublishers.ofByteArray(multipartBody(request, boundary));
                contentType = "multipart/form-data; boundary=" + boundary;
            } else if (request.formFields() != null) {
                StringBuilder form = new StringBuilder();
                request.formFields().forEach((k, v) -> form.append(form.length() == 0 ? "" : "&")
                        .append(formEncode(k)).append('=').append(formEncode(v)));
                body = HttpRequest.BodyPublishers.ofString(form.toString());
                contentType = "application/x-www-form-urlencoded";
            }
        } catch (JsonProcessingException e) {
            throw new NovaClientValidationException("Request body cannot be serialized: " + e.getOriginalMessage());
        }
        Duration timeout = options.timeout() != null ? options.timeout() : config.requestTimeout();
        try {
            HttpRequest.Builder builder = HttpRequest.newBuilder(URI.create(url)).timeout(timeout)
                    .method(request.method().name(), body);
            headers.forEach(builder::header);
            if (contentType != null) {
                builder.header("Content-Type", contentType);
            }
            return builder.build();
        } catch (IllegalArgumentException e) {
            throw new NovaClientValidationException("Invalid request: " + e.getMessage());
        }
    }

    private static byte[] multipartBody(ApiRequest request, String boundary) {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        String dashes = "--" + boundary + "\r\n";
        request.formFields().forEach((name, value) -> write(out, dashes
                + "Content-Disposition: form-data; name=\"" + quote(name) + "\"\r\n\r\n" + value + "\r\n"));
        write(out, dashes + "Content-Disposition: form-data; name=\"file\"; filename=\"" + quote(request.file().filename())
                + "\"\r\nContent-Type: " + request.file().contentType() + "\r\n\r\n");
        out.writeBytes(request.file().content());
        write(out, "\r\n--" + boundary + "--\r\n");
        return out.toByteArray();
    }

    private static void write(ByteArrayOutputStream out, String text) {
        out.writeBytes(text.getBytes(StandardCharsets.UTF_8));
    }

    private static String quote(String value) {
        return value.replace("\"", "%22").replace("\r", "").replace("\n", "");
    }

    private Map<String, String> headers() {
        Map<String, String> headers = new java.util.LinkedHashMap<>();
        headers.put("Accept", "application/json");
        headers.put("User-Agent", "Nova-Java-SDK/" + Version.VERSION);
        headers.putAll(config.defaultHeaders());
        String bearer = bearer();
        if (bearer != null) {
            headers.put("Authorization", "Bearer " + bearer);
        }
        String tenant = options.tenantId() != null ? NovaConfig.normalizeTenantId(options.tenantId()) : config.tenantId();
        if (tenant != null) {
            headers.put("X-Tenant-ID", tenant);
        }
        if (options.correlationId() != null && !options.correlationId().isBlank()) {
            headers.put("X-Correlation-ID", options.correlationId().strip());
        }
        headers.putAll(options.headers());
        return headers;
    }

    private String bearer() {
        return config.bearerCredential();
    }

    // -- execution ----------------------------------------------------------------------------

    private record Raw(int status, byte[] body, java.net.http.HttpHeaders headers) {
    }

    private Raw execute(ApiRequest request) {
        String url = buildUrl(request);
        Map<String, String> headers = headers();
        HttpRequest httpRequest = buildRequest(request, url, headers);
        String correlationId = headers.get("X-Correlation-ID");
        boolean safe = request.allowRetry() != null ? request.allowRetry() : request.method().idempotent();
        int maxAttempts = safe ? config.maxRetries() + 1 : 1;

        for (int attempt = 0; attempt < maxAttempts; attempt++) {
            boolean last = attempt >= maxAttempts - 1;
            HttpResponse<byte[]> response;
            try {
                response = client.send(httpRequest, HttpResponse.BodyHandlers.ofByteArray());
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new NovaAbortedException("Request was interrupted.", e);
            } catch (HttpConnectTimeoutException e) {
                if (!last) {
                    pause(backoff(attempt, null), request, "connect timeout");
                    continue;
                }
                throw new NovaConnectionException("Failed to connect to the Nova API: connect timed out.", correlationId, e);
            } catch (HttpTimeoutException e) {
                if (!last) {
                    pause(backoff(attempt, null), request, "timeout");
                    continue;
                }
                throw new NovaTimeoutException(
                        "Request to the Nova API timed out after " + httpRequest.timeout().orElse(config.requestTimeout()) + ".",
                        correlationId, e);
            } catch (IOException e) {
                if (!last) {
                    pause(backoff(attempt, null), request, "connection error");
                    continue;
                }
                throw new NovaConnectionException("Failed to connect to the Nova API: " + describe(e), correlationId, e);
            }

            int status = response.statusCode();
            if (status >= 200 && status < 300) {
                return new Raw(status, response.body(), response.headers());
            }
            if (status >= 300 && status < 400) {
                throw redirect(response);
            }
            if (!last && RETRYABLE.contains(status)) {
                pause(backoff(attempt, retryAfter(response)), request, "HTTP " + status);
                continue;
            }
            throw errorFrom(response);
        }
        throw new NovaException("Request terminated without a response.");
    }

    private static String describe(IOException e) {
        return e.getMessage() == null ? e.getClass().getSimpleName() : e.getMessage();
    }

    private void pause(Duration delay, ApiRequest request, String reason) {
        LOG.log(System.Logger.Level.WARNING, "Nova {0} {1}: {2}; retrying in {3} ms",
                request.method(), request.template(), reason, delay.toMillis());
        try {
            Thread.sleep(delay.toMillis());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new NovaAbortedException("Request was interrupted while waiting to retry.", e);
        }
    }

    private Duration backoff(int attempt, Duration retryAfter) {
        if (retryAfter != null) {
            return retryAfter.compareTo(MAX_RETRY_AFTER) > 0 ? MAX_RETRY_AFTER : retryAfter;
        }
        double millis = config.retryBackoff().toMillis() * Math.pow(2, attempt);
        if (config.retryJitter()) {
            millis *= 0.5 + ThreadLocalRandom.current().nextDouble() * 0.5;
        }
        return Duration.ofMillis((long) Math.min(MAX_RETRY_AFTER.toMillis(), Math.max(50, millis)));
    }

    private static Duration retryAfter(HttpResponse<?> response) {
        return response.headers().firstValue("Retry-After").map(v -> {
            try {
                return Duration.ofMillis((long) (Math.max(0, Double.parseDouble(v.trim())) * 1000));
            } catch (NumberFormatException e) {
                return null;
            }
        }).orElse(null);
    }

    // -- responses ----------------------------------------------------------------------------

    private ApiResult parseSuccess(Raw raw) {
        String correlationId = raw.headers().firstValue("X-Correlation-ID").orElse(null);
        ObjectNode meta = mapper.createObjectNode();
        if (correlationId != null) {
            meta.put("correlation_id", correlationId);
        }
        String ok = "Operation completed successfully.";
        if (raw.status() == 204 || raw.body().length == 0) {
            return new ApiResult(null, true, ok, meta);
        }
        String text = new String(raw.body(), StandardCharsets.UTF_8);
        String contentType = raw.headers().firstValue("Content-Type").orElse("");
        if (contentType.contains("text/csv")) {
            return new ApiResult(TextNode.valueOf(text), true, "CSV export generated.", meta);
        }
        JsonNode payload;
        try {
            payload = mapper.readTree(text);
        } catch (JsonProcessingException e) {
            if (contentType.toLowerCase(java.util.Locale.ROOT).contains("json")) {
                // The server declared JSON but sent something else: never report that as success.
                throw new com.infimatrix.nova.errors.NovaApiException(
                        "Invalid JSON in HTTP " + raw.status() + " response.", raw.status(), "INVALID_RESPONSE", null,
                        correlationId);
            }
            return new ApiResult(TextNode.valueOf(text), true, "Raw response received.", meta);
        }
        if (payload != null && payload.isObject() && payload.has("success") && payload.has("data")) {
            ObjectNode envelopeMeta = payload.get("meta") != null && payload.get("meta").isObject()
                    ? ((ObjectNode) payload.get("meta")).deepCopy() : mapper.createObjectNode();
            if ((!envelopeMeta.hasNonNull("correlation_id")) && correlationId != null) {
                envelopeMeta.put("correlation_id", correlationId);
            }
            JsonNode data = payload.get("data");
            return new ApiResult(data == null || data instanceof NullNode ? null : data,
                    payload.path("success").asBoolean(true),
                    payload.path("message").isTextual() ? payload.get("message").asText() : ok, envelopeMeta);
        }
        return new ApiResult(payload, true, ok, meta);
    }

    private com.infimatrix.nova.errors.NovaApiException redirect(HttpResponse<byte[]> response) {
        String location = sanitizeLocation(response.headers().firstValue("Location").orElse(null));
        return ApiErrors.map(response.statusCode(),
                "Unexpected HTTP " + response.statusCode() + " redirect" + (location == null ? "" : " to " + location) + ".",
                null, null, response.headers().firstValue("X-Correlation-ID").orElse(null), null, location);
    }

    static String sanitizeLocation(String location) {
        if (location == null || location.isBlank()) {
            return null;
        }
        // Textual on purpose: java.net.URI treats "user:se@cret@host" as a registry-based authority and reports no
        // userinfo, which would leave the credentials in place. Userinfo ends at the LAST '@' of the authority
        // (RFC 3986 3.2).
        String stripped = location.strip();
        int schemeEnd = stripped.indexOf("://");
        if (schemeEnd < 0) {
            return stripped;
        }
        int start = schemeEnd + 3;
        int end = start;
        while (end < stripped.length() && "/?#".indexOf(stripped.charAt(end)) < 0) {
            end++;
        }
        int at = stripped.substring(start, end).lastIndexOf('@');
        if (at < 0) {
            return stripped;
        }
        return stripped.substring(0, start) + stripped.substring(start + at + 1);
    }

    private com.infimatrix.nova.errors.NovaApiException errorFrom(HttpResponse<byte[]> response) {
        String correlationId = response.headers().firstValue("X-Correlation-ID").orElse(null);
        String text = new String(response.body(), StandardCharsets.UTF_8);
        String message = null;
        String code = null;
        Object details = null;
        try {
            JsonNode payload = mapper.readTree(text);
            if (payload != null && payload.isObject()) {
                JsonNode meta = payload.get("meta");
                if (meta != null && meta.hasNonNull("correlation_id")) {
                    correlationId = meta.get("correlation_id").asText();
                }
                JsonNode err = payload.hasNonNull("error") ? payload.get("error") : payload.get("errors");
                if (err != null && err.isObject()) {
                    code = err.hasNonNull("code") ? err.get("code").asText() : null;
                    message = err.hasNonNull("message") ? err.get("message").asText() : null;
                    details = err.hasNonNull("details") ? mapper.convertValue(err.get("details"), Object.class) : null;
                } else if (err != null && err.isTextual()) {
                    message = err.asText(); // legacy bodies such as {"error": "Tenant context required."}
                }
                if (message == null || message.isEmpty()) {
                    JsonNode top = payload.hasNonNull("message") ? payload.get("message") : payload.get("detail");
                    message = top != null && top.isTextual() ? top.asText() : null;
                }
                if (details == null) {
                    Map<String, Object> rest = new java.util.LinkedHashMap<>();
                    payload.properties().forEach(e -> {
                        if (!SKIPPED_ERROR_KEYS.contains(e.getKey())) {
                            rest.put(e.getKey(), mapper.convertValue(e.getValue(), Object.class));
                        }
                    });
                    details = rest;
                }
            } else if (payload != null && payload.isArray()) {
                details = Map.of("errors", mapper.convertValue(payload, Object.class));
                message = "Validation failed for request data.";
            }
        } catch (JsonProcessingException e) {
            message = summarize(text, response.statusCode());
        }
        if (message == null || message.isEmpty()) {
            message = summarize(text, response.statusCode());
        }
        return ApiErrors.map(response.statusCode(), message, code, details, correlationId, retryAfter(response), null);
    }

    /** Reduces a non-JSON or HTML error body to a short, safe summary. */
    static String summarize(String text, int status) {
        String raw = text == null ? "" : text.strip();
        if (raw.isEmpty()) {
            return "HTTP " + status + " Error";
        }
        String lower = raw.toLowerCase(Locale.ROOT);
        if (lower.contains("<html") || lower.contains("<!doctype html") || lower.contains("<head") || lower.contains("<body")) {
            java.util.regex.Matcher m = java.util.regex.Pattern
                    .compile("<title>(.*?)</title>", java.util.regex.Pattern.CASE_INSENSITIVE | java.util.regex.Pattern.DOTALL)
                    .matcher(raw);
            if (m.find()) {
                String title = m.group(1).replaceAll("\\s+", " ").strip();
                if (!title.isEmpty() && title.length() <= 120) {
                    return "HTTP " + status + " Error: " + title;
                }
            }
            return "HTTP " + status + " Error (HTML response received)";
        }
        String collapsed = raw.replaceAll("\\s+", " ");
        return collapsed.length() > 200 ? collapsed.substring(0, 197) + "..." : collapsed;
    }
}
