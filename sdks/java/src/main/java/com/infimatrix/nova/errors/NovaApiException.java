package com.infimatrix.nova.errors;

/** Base class for HTTP 4xx and 5xx responses and unexpected redirects. */
public class NovaApiException extends NovaException {
    private static final long serialVersionUID = 1L;

    /** Creates the exception from an API response. */
    public NovaApiException(
            String message, int statusCode, String errorCode, Object details, String correlationId) {
        super(message, statusCode, errorCode, details, correlationId, null);
    }
}
