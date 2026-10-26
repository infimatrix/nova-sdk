package com.infimatrix.nova.http;

import com.fasterxml.jackson.databind.JsonNode;

/**
 * An unwrapped API response.
 *
 * @param data the {@code data} payload ({@code null} for empty responses; a text node for CSV or non-JSON bodies)
 * @param success the envelope's {@code success} flag
 * @param message the envelope's {@code message}
 * @param meta the envelope's {@code meta} object (never {@code null})
 */
public record ApiResult(JsonNode data, boolean success, String message, JsonNode meta) {

    /** The server correlation id from {@code meta}, or {@code null}. */
    public String correlationId() {
        JsonNode id = meta == null ? null : meta.get("correlation_id");
        return id == null || id.isNull() ? null : id.asText();
    }
}
