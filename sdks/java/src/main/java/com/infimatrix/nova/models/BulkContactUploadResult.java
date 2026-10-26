// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;

/**
 * BulkContactUploadResult model.
 *
 * @param message JSON property message.
 * @param createdCount JSON property created_count.
 * @param errors Per-row failures: {row, error}.
 * @param contacts JSON property contacts.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record BulkContactUploadResult(
    @JsonProperty("message") String message,
    @JsonProperty("created_count") Long createdCount,
    @JsonProperty("errors") List<Map<String, Object>> errors,
    @JsonProperty("contacts") List<Contact> contacts
) {
}
