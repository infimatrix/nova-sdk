package com.infimatrix.nova.errors;

import java.time.Duration;

/** HTTP 429: rate limit exceeded. */
public class NovaRateLimitException extends NovaApiException {
    private static final long serialVersionUID = 1L;

    private final transient Duration retryAfter;

    /** Creates the exception from an API response. */
    public NovaRateLimitException(
            String message,
            int statusCode,
            String errorCode,
            Object details,
            String correlationId,
            Duration retryAfter) {
        super(message, statusCode, errorCode, details, correlationId);
        this.retryAfter = retryAfter;
    }

    /** Returns the delay requested by the {@code Retry-After} header, or {@code null}. */
    public Duration retryAfter() {
        return retryAfter;
    }
}
