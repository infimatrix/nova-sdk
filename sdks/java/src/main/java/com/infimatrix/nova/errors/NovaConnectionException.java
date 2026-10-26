package com.infimatrix.nova.errors;

/** A network, DNS or socket failure; the request may not have reached the server. */
public class NovaConnectionException extends NovaException {
    private static final long serialVersionUID = 1L;

    /** Creates the exception. */
    public NovaConnectionException(String message, String correlationId, Throwable cause) {
        super(message, null, "CONNECTION_ERROR", null, correlationId, cause);
    }
}
