package com.infimatrix.nova.errors;

/**
 * Base class of every exception thrown by the Nova SDK.
 *
 * <p>Messages and string forms never contain credentials, authorization headers or request bodies.
 * The exception is unchecked so that SDK calls compose with lambdas and streams.
 */
public class NovaException extends RuntimeException {
    private static final long serialVersionUID = 1L;

    private final Integer statusCode;
    private final String errorCode;
    private final transient Object details;
    private final String correlationId;
    private final String rawMessage;

    /**
     * Creates an exception.
     *
     * @param message human readable message without the metadata suffix
     * @param statusCode HTTP status, or {@code null} when not caused by an API response
     * @param errorCode machine readable code; {@code SDK_ERROR} when {@code null}
     * @param details structured details, for example field-level validation errors (may be {@code null})
     * @param correlationId correlation id for support and log tracing (may be {@code null})
     * @param cause underlying cause (may be {@code null})
     */
    public NovaException(
            String message,
            Integer statusCode,
            String errorCode,
            Object details,
            String correlationId,
            Throwable cause) {
        super(format(message, statusCode, errorCode, correlationId), cause);
        this.rawMessage = message;
        this.statusCode = statusCode;
        this.errorCode = errorCode == null ? "SDK_ERROR" : errorCode;
        this.details = details;
        this.correlationId = correlationId;
    }

    /** Creates an SDK-level exception with the {@code SDK_ERROR} code. */
    public NovaException(String message) {
        this(message, null, null, null, null, null);
    }

    private static String format(String message, Integer status, String code, String correlationId) {
        StringBuilder meta = new StringBuilder();
        if (status != null) {
            meta.append("status=").append(status);
        }
        if (code != null) {
            meta.append(meta.length() > 0 ? ", " : "").append("code=").append(code);
        }
        if (correlationId != null) {
            meta.append(meta.length() > 0 ? ", " : "").append("correlation_id=").append(correlationId);
        }
        return meta.length() == 0 ? message : message + " (" + meta + ")";
    }

    /** Returns the HTTP status code, or {@code null} if the error did not come from an API response. */
    public Integer statusCode() {
        return statusCode;
    }

    /** Returns the machine readable error code (API provided, or an SDK code such as {@code CONNECTION_ERROR}). */
    public String errorCode() {
        return errorCode;
    }

    /** Returns structured error details (typically a {@code Map} of field errors), or {@code null}. */
    public Object details() {
        return details;
    }

    /** Returns the correlation id reported by the server, or {@code null}. */
    public String correlationId() {
        return correlationId;
    }

    /** Returns the message without the {@code (status=..., code=...)} suffix. */
    public String rawMessage() {
        return rawMessage;
    }
}
