// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * WebhookTestDispatch model.
 *
 * @param success JSON property success.
 * @param message JSON property message.
 * @param webhookId JSON property webhook_id.
 * @param taskId JSON property task_id.
 * @param url JSON property url.
 * @param eventType JSON property event_type.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record WebhookTestDispatch(
    @JsonProperty("success") Boolean success,
    @JsonProperty("message") String message,
    @JsonProperty("webhook_id") String webhookId,
    @JsonProperty("task_id") String taskId,
    @JsonProperty("url") String url,
    @JsonProperty("event_type") String eventType
) {
}
