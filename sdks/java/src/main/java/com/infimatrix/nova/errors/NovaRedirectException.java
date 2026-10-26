package com.infimatrix.nova.errors;

import java.util.Map;

/** An unexpected HTTP 3xx response. Redirects are never followed so credentials cannot leak to another host. */
public class NovaRedirectException extends NovaApiException {
    private static final long serialVersionUID = 1L;

    private final String location;

    /** Creates the exception; {@code location} must already have embedded credentials removed. */
    public NovaRedirectException(String message, int statusCode, String location, String correlationId) {
        super(
                message,
                statusCode,
                "UNEXPECTED_REDIRECT",
                location == null ? Map.of() : Map.of("location", location),
                correlationId);
        this.location = location;
    }

    /** Returns the sanitized redirect target, or {@code null}. */
    public String location() {
        return location;
    }
}
