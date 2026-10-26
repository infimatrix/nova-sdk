package com.infimatrix.nova.errors;

/** HTTP 401: missing, invalid or expired credentials. */
public class NovaAuthenticationException extends NovaApiException {
    private static final long serialVersionUID = 1L;

    /** Creates the exception from an API response. */
    public NovaAuthenticationException(
            String message, int statusCode, String errorCode, Object details, String correlationId) {
        super(message, statusCode, errorCode, details, correlationId);
    }
}
