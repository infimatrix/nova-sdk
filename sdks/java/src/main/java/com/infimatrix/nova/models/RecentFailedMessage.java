// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * RecentFailedMessage model.
 *
 * @param id JSON property id.
 * @param recipientEmail JSON property recipient_email.
 * @param subject JSON property subject.
 * @param status JSON property status. Optional.
 * @param metadata JSON property metadata. Optional.
 * @param createdAt JSON property created_at.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record RecentFailedMessage(
    @JsonProperty("id") String id,
    @JsonProperty("recipient_email") String recipientEmail,
    @JsonProperty("subject") String subject,
    @JsonProperty("status") String status,
    @JsonProperty("metadata") Object metadata,
    @JsonProperty("created_at") String createdAt
) {
}
