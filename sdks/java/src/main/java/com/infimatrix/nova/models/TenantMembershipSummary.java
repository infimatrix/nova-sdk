// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * TenantMembershipSummary model.
 *
 * @param id JSON property id.
 * @param name JSON property name.
 * @param slug JSON property slug.
 * @param website JSON property website.
 * @param logoUrl JSON property logo_url.
 * @param role JSON property role.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record TenantMembershipSummary(
    @JsonProperty("id") String id,
    @JsonProperty("name") String name,
    @JsonProperty("slug") String slug,
    @JsonProperty("website") String website,
    @JsonProperty("logo_url") String logoUrl,
    @JsonProperty("role") String role
) {
}
