package com.infimatrix.nova.errors;

/** HTTP 403: authenticated but not permitted. */
public class NovaPermissionException extends NovaApiException {
    private static final long serialVersionUID = 1L;

    /** Creates the exception from an API response. */
    public NovaPermissionException(
            String message, int statusCode, String errorCode, Object details, String correlationId) {
        super(message, statusCode, errorCode, details, correlationId);
    }
}
