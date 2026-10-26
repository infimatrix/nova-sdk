package com.infimatrix.nova;

import com.infimatrix.nova.errors.NovaClientValidationException;
import java.net.URI;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;
import java.util.regex.Pattern;

/**
 * Validated, immutable client configuration.
 *
 * <p>Credentials are never included in {@link #toString()}.
 */
public final class NovaConfig {
    private static final Pattern UUID_PATTERN =
            Pattern.compile("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$");

    private final String baseUrl;
    private final String apiKey;
    private final String accessToken;
    private final String tenantId;
    private final Duration connectTimeout;
    private final Duration requestTimeout;
    private final int maxRetries;
    private final Duration retryBackoff;
    private final boolean retryJitter;
    private final Map<String, String> defaultHeaders;

    NovaConfig(
            String baseUrl,
            String apiKey,
            String accessToken,
            String tenantId,
            Duration connectTimeout,
            Duration requestTimeout,
            int maxRetries,
            Duration retryBackoff,
            boolean retryJitter,
            Map<String, String> defaultHeaders) {
        this.baseUrl = normalizeBaseUrl(baseUrl);
        this.apiKey = cleanCredential(apiKey);
        this.accessToken = cleanCredential(accessToken);
        this.tenantId = tenantId == null || tenantId.isBlank() ? null : normalizeTenantId(tenantId);
        this.connectTimeout = positive(connectTimeout, "connectTimeout");
        this.requestTimeout = positive(requestTimeout, "requestTimeout");
        if (maxRetries < 0 || maxRetries > 10) {
            throw new NovaClientValidationException("maxRetries must be between 0 and 10, got " + maxRetries + ".");
        }
        this.maxRetries = maxRetries;
        if (retryBackoff == null || retryBackoff.isNegative()) {
            throw new NovaClientValidationException("retryBackoff must be a non-negative duration.");
        }
        this.retryBackoff = retryBackoff;
        this.retryJitter = retryJitter;
        this.defaultHeaders = Map.copyOf(new LinkedHashMap<>(defaultHeaders));
    }

    private static Duration positive(Duration value, String name) {
        if (value == null || value.isZero() || value.isNegative()) {
            throw new NovaClientValidationException(name + " must be a positive duration.");
        }
        return value;
    }

    static String normalizeBaseUrl(String raw) {
        if (raw == null || raw.isBlank()) {
            throw new NovaClientValidationException("baseUrl must be a non-empty string.");
        }
        URI uri;
        try {
            uri = URI.create(raw.trim());
        } catch (IllegalArgumentException e) {
            throw new NovaClientValidationException("Invalid baseUrl: must be an absolute http(s) URL.");
        }
        String scheme = uri.getScheme() == null ? "" : uri.getScheme().toLowerCase(Locale.ROOT);
        if (!scheme.equals("http") && !scheme.equals("https")) {
            throw new NovaClientValidationException("Invalid baseUrl scheme '" + scheme + "'. Must be 'http' or 'https'.");
        }
        if (uri.getHost() == null) {
            throw new NovaClientValidationException("Invalid baseUrl: it must include a host.");
        }
        String url = raw.trim().replaceAll("/+$", "");
        return url.replaceAll("/api(/v1)?$", "");
    }

    /** Strips whitespace and any leading {@code Bearer } prefix; returns {@code null} when nothing remains. */
    static String cleanCredential(String value) {
        if (value == null) {
            return null;
        }
        String cleaned = value.trim();
        while (true) {
            String lower = cleaned.toLowerCase(Locale.ROOT);
            if (lower.equals("bearer")) {
                return null;
            }
            if (!lower.startsWith("bearer ")) {
                break;
            }
            cleaned = cleaned.substring(7).trim();
        }
        return cleaned.isEmpty() ? null : cleaned;
    }

    /** Validates a tenant id and returns its canonical lower-case form. */
    public static String normalizeTenantId(String value) {
        String trimmed = value == null ? "" : value.trim();
        if (!UUID_PATTERN.matcher(trimmed).matches()) {
            throw new NovaClientValidationException("tenant_id must be a valid UUID string, got '" + value + "'.");
        }
        return UUID.fromString(trimmed).toString();
    }

    private static String redact(String credential) {
        if (credential == null) {
            return "<none>";
        }
        return credential.length() <= 12 ? "[REDACTED]" : credential.substring(0, 8) + "...[REDACTED]";
    }

    /** API origin without trailing slash or {@code /api/v1}. */
    public String baseUrl() {
        return baseUrl;
    }

    /** Default tenant id, or {@code null}. */
    public String tenantId() {
        return tenantId;
    }

    /** Connect timeout. */
    public Duration connectTimeout() {
        return connectTimeout;
    }

    /** Per-attempt request timeout. */
    public Duration requestTimeout() {
        return requestTimeout;
    }

    /** Maximum retries of idempotent requests. */
    public int maxRetries() {
        return maxRetries;
    }

    /** Backoff base. */
    public Duration retryBackoff() {
        return retryBackoff;
    }

    /** Whether backoff is randomized. */
    public boolean retryJitter() {
        return retryJitter;
    }

    /** Headers added to every request. */
    public Map<String, String> defaultHeaders() {
        return defaultHeaders;
    }

    /** The bearer credential in effect: the API key wins over the access token; {@code null} if none. */
    public String bearerCredential() {
        return apiKey != null ? apiKey : accessToken;
    }

    String apiKey() {
        return apiKey;
    }

    String accessToken() {
        return accessToken;
    }

    /** Returns a copy with another default tenant. */
    NovaConfig withTenant(String newTenantId) {
        return new NovaConfig(baseUrl, apiKey, accessToken, newTenantId, connectTimeout, requestTimeout,
                maxRetries, retryBackoff, retryJitter, defaultHeaders);
    }

    /** Returns a copy with another access token. */
    NovaConfig withAccessToken(String token) {
        return new NovaConfig(baseUrl, apiKey, token, tenantId, connectTimeout, requestTimeout,
                maxRetries, retryBackoff, retryJitter, defaultHeaders);
    }

    /** Returns a copy with another API key. */
    NovaConfig withApiKey(String key) {
        return new NovaConfig(baseUrl, key, accessToken, tenantId, connectTimeout, requestTimeout,
                maxRetries, retryBackoff, retryJitter, defaultHeaders);
    }

    @Override
    public String toString() {
        return "NovaConfig(baseUrl=" + baseUrl + ", apiKey=" + redact(apiKey) + ", accessToken=" + redact(accessToken)
                + ", tenantId=" + tenantId + ", connectTimeout=" + connectTimeout + ", requestTimeout=" + requestTimeout
                + ", maxRetries=" + maxRetries + ")";
    }
}
