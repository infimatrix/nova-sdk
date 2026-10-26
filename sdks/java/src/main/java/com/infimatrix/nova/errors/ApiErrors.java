package com.infimatrix.nova.errors;

import java.time.Duration;

/** Maps HTTP status codes to the typed exceptions. */
public final class ApiErrors {
    private ApiErrors() {
    }

    /**
     * Maps a response status to the matching exception.
     *
     * @param status HTTP status code (4xx, 5xx or an unexpected 3xx)
     * @param message error message
     * @param errorCode API error code, or {@code null}
     * @param details structured details, or {@code null}
     * @param correlationId correlation id, or {@code null}
     * @param retryAfter value of {@code Retry-After}, or {@code null}
     * @param location sanitized redirect location for 3xx responses, or {@code null}
     * @return the exception to throw
     */
    public static NovaApiException map(
            int status,
            String message,
            String errorCode,
            Object details,
            String correlationId,
            Duration retryAfter,
            String location) {
        String msg = message == null || message.isBlank() ? "API request failed with status " + status + "." : message;
        if (status >= 300 && status < 400) {
            return new NovaRedirectException(msg, status, location, correlationId);
        }
        switch (status) {
            case 401:
                return new NovaAuthenticationException(msg, status, or(errorCode, "API_ERROR"), details, correlationId);
            case 403:
                return new NovaPermissionException(msg, status, or(errorCode, "API_ERROR"), details, correlationId);
            case 404:
                return new NovaNotFoundException(msg, status, or(errorCode, "API_ERROR"), details, correlationId);
            case 400:
                return new NovaValidationException(msg, status, or(errorCode, "API_ERROR"), details, correlationId);
            case 429:
                return new NovaRateLimitException(
                        msg, status, or(errorCode, "RATE_LIMIT_EXCEEDED"), details, correlationId, retryAfter);
            default:
                if (status >= 500) {
                    return new NovaServerException(msg, status, or(errorCode, "API_ERROR"), details, correlationId);
                }
                return new NovaApiException(msg, status, errorCode, details, correlationId);
        }
    }

    private static String or(String value, String fallback) {
        return value == null ? fallback : value;
    }
}
