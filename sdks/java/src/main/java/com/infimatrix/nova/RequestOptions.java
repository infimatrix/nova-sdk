package com.infimatrix.nova;

import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Per-call overrides, applied with {@link NovaClient#with(RequestOptions)}.
 *
 * <p>Instances are immutable.
 */
public final class RequestOptions {
    private static final RequestOptions NONE = new RequestOptions(new Builder());

    private final String tenantId;
    private final Map<String, String> headers;
    private final String correlationId;
    private final Duration timeout;

    private RequestOptions(Builder b) {
        this.tenantId = b.tenantId;
        this.headers = Map.copyOf(b.headers);
        this.correlationId = b.correlationId;
        this.timeout = b.timeout;
    }

    /** Returns options that change nothing. */
    public static RequestOptions none() {
        return NONE;
    }

    /** Returns a new builder. */
    public static Builder builder() {
        return new Builder();
    }

    /** Tenant UUID sent as {@code X-Tenant-ID}, or {@code null} to use the client default. */
    public String tenantId() {
        return tenantId;
    }

    /** Extra headers for the call. */
    public Map<String, String> headers() {
        return headers;
    }

    /** Value sent as {@code X-Correlation-ID}, or {@code null}. */
    public String correlationId() {
        return correlationId;
    }

    /** Per-attempt request timeout override, or {@code null}. */
    public Duration timeout() {
        return timeout;
    }

    /** Builder for {@link RequestOptions}. */
    public static final class Builder {
        private String tenantId;
        private final Map<String, String> headers = new LinkedHashMap<>();
        private String correlationId;
        private Duration timeout;

        private Builder() {
        }

        /** Sets the tenant UUID for the call. */
        public Builder tenantId(String value) {
            this.tenantId = value;
            return this;
        }

        /** Adds a header. */
        public Builder header(String name, String value) {
            this.headers.put(name, value);
            return this;
        }

        /** Sets the correlation id. */
        public Builder correlationId(String value) {
            this.correlationId = value;
            return this;
        }

        /** Overrides the per-attempt request timeout. */
        public Builder timeout(Duration value) {
            this.timeout = value;
            return this;
        }

        /** Builds the options. */
        public RequestOptions build() {
            return new RequestOptions(this);
        }
    }
}
