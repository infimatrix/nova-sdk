package com.infimatrix.nova.errors;

/** HTTP 400: the server rejected the request payload or parameters. */
public class NovaValidationException extends NovaApiException {
    private static final long serialVersionUID = 1L;

    /** Creates the exception from an API response. */
    public NovaValidationException(
            String message, int statusCode, String errorCode, Object details, String correlationId) {
        super(message, statusCode, errorCode, details, correlationId);
    }
}
