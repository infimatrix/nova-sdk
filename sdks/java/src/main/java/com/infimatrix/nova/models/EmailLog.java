// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * EmailLog model.
 *
 * @param id JSON property id.
 * @param messageId JSON property message_id.
 * @param senderName JSON property sender_name.
 * @param senderEmail JSON property sender_email.
 * @param receiverName JSON property receiver_name.
 * @param receiverEmail JSON property receiver_email.
 * @param templateName JSON property template_name.
 * @param subject JSON property subject.
 * @param note JSON property note.
 * @param status JSON property status.
 * @param createdAt JSON property created_at.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record EmailLog(
    @JsonProperty("id") String id,
    @JsonProperty("message_id") String messageId,
    @JsonProperty("sender_name") String senderName,
    @JsonProperty("sender_email") String senderEmail,
    @JsonProperty("receiver_name") String receiverName,
    @JsonProperty("receiver_email") String receiverEmail,
    @JsonProperty("template_name") String templateName,
    @JsonProperty("subject") String subject,
    @JsonProperty("note") String note,
    @JsonProperty("status") String status,
    @JsonProperty("created_at") String createdAt
) {
}
