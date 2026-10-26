// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Serializer for creating a new API Key for the authenticated user.
 *
 * @param id JSON property id.
 * @param name JSON property name. Optional.
 * @param keyPrefix JSON property key_prefix.
 * @param apiKey JSON property api_key.
 * @param isActive JSON property is_active.
 * @param expiresAt JSON property expires_at. Optional.
 * @param createdAt JSON property created_at.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record APIKeyCreate(
    @JsonProperty("id") String id,
    @JsonProperty("name") String name,
    @JsonProperty("key_prefix") String keyPrefix,
    @JsonProperty("api_key") String apiKey,
    @JsonProperty("is_active") Boolean isActive,
    @JsonProperty("expires_at") String expiresAt,
    @JsonProperty("created_at") String createdAt
) {
}
