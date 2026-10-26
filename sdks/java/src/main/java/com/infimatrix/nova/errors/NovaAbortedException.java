package com.infimatrix.nova.errors;

/** The calling thread was interrupted while a request or retry wait was in progress. */
public class NovaAbortedException extends NovaException {
    private static final long serialVersionUID = 1L;

    /** Creates the exception. */
    public NovaAbortedException(String message, Throwable cause) {
        super(message, null, "REQUEST_ABORTED", null, null, cause);
    }
}
