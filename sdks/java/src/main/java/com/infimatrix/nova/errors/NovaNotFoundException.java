package com.infimatrix.nova.errors;

/** HTTP 404: the resource does not exist in the active tenant. */
public class NovaNotFoundException extends NovaApiException {
    private static final long serialVersionUID = 1L;

    /** Creates the exception from an API response. */
    public NovaNotFoundException(
            String message, int statusCode, String errorCode, Object details, String correlationId) {
        super(message, statusCode, errorCode, details, correlationId);
    }
}
