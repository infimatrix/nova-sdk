package com.infimatrix.nova.errors;

/** A request was rejected by the SDK before it was sent (for example an empty identifier). */
public class NovaClientValidationException extends NovaException {
    private static final long serialVersionUID = 1L;

    /** Creates the exception. */
    public NovaClientValidationException(String message) {
        super(message, null, "SDK_ERROR", null, null, null);
    }
}
