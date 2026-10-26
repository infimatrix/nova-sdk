package com.infimatrix.nova.errors;

/** The request exceeded the configured request timeout. */
public class NovaTimeoutException extends NovaException {
    private static final long serialVersionUID = 1L;

    /** Creates the exception. */
    public NovaTimeoutException(String message, String correlationId, Throwable cause) {
        super(message, null, "REQUEST_TIMEOUT", null, correlationId, cause);
    }
}
