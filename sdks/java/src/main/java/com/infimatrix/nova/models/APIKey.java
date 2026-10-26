// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Serializer for listing and reading user API Key records (without exposing raw secret key).
 *
 * @param id JSON property id.
 * @param name JSON property name.
 * @param keyPrefix JSON property key_prefix.
 * @param isActive JSON property is_active.
 * @param createdAt JSON property created_at.
 * @param expiresAt JSON property expires_at.
 * @param lastUsedAt JSON property last_used_at.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record APIKey(
    @JsonProperty("id") String id,
    @JsonProperty("name") String name,
    @JsonProperty("key_prefix") String keyPrefix,
    @JsonProperty("is_active") Boolean isActive,
    @JsonProperty("created_at") String createdAt,
    @JsonProperty("expires_at") String expiresAt,
    @JsonProperty("last_used_at") String lastUsedAt
) {
}
