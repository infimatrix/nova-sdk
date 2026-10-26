// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Tenant model.
 *
 * @param id JSON property id.
 * @param name JSON property name.
 * @param slug JSON property slug.
 * @param website Workspace domain / website URL Optional.
 * @param logoUrl Workspace logo / favicon URL Optional.
 * @param status JSON property status. Optional.
 * @param isActive JSON property is_active.
 * @param createdAt JSON property created_at.
 * @param updatedAt JSON property updated_at.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record Tenant(
    @JsonProperty("id") String id,
    @JsonProperty("name") String name,
    @JsonProperty("slug") String slug,
    @JsonProperty("website") String website,
    @JsonProperty("logo_url") String logoUrl,
    @JsonProperty("status") String status,
    @JsonProperty("is_active") Boolean isActive,
    @JsonProperty("created_at") String createdAt,
    @JsonProperty("updated_at") String updatedAt
) {
}
