// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * WebhookEndpoint model.
 *
 * @param id JSON property id.
 * @param name JSON property name.
 * @param url JSON property url.
 * @param secret Secret key used for HMAC payload signature verification
 * @param secretMasked JSON property secret_masked.
 * @param events List of subscribed event keys e.g. ['contact.created', 'email.delivered'] Optional.
 * @param isActive JSON property is_active. Optional.
 * @param createdAt JSON property created_at.
 * @param updatedAt JSON property updated_at.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record WebhookEndpoint(
    @JsonProperty("id") String id,
    @JsonProperty("name") String name,
    @JsonProperty("url") String url,
    @JsonProperty("secret") String secret,
    @JsonProperty("secret_masked") String secretMasked,
    @JsonProperty("events") Object events,
    @JsonProperty("is_active") Boolean isActive,
    @JsonProperty("created_at") String createdAt,
    @JsonProperty("updated_at") String updatedAt
) {
}
