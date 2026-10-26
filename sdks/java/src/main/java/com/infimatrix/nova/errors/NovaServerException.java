package com.infimatrix.nova.errors;

/** HTTP 5xx: the Nova server failed. */
public class NovaServerException extends NovaApiException {
    private static final long serialVersionUID = 1L;

    /** Creates the exception from an API response. */
    public NovaServerException(
            String message, int statusCode, String errorCode, Object details, String correlationId) {
        super(message, statusCode, errorCode, details, correlationId);
    }
}
