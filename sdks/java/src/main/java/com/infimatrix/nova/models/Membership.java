// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Membership model.
 *
 * @param id JSON property id.
 * @param userId JSON property user_id.
 * @param userEmail JSON property user_email.
 * @param userFirstName JSON property user_first_name.
 * @param userLastName JSON property user_last_name.
 * @param role JSON property role. Optional.
 * @param status JSON property status. Optional.
 * @param createdAt JSON property created_at.
 * @param updatedAt JSON property updated_at.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record Membership(
    @JsonProperty("id") String id,
    @JsonProperty("user_id") String userId,
    @JsonProperty("user_email") String userEmail,
    @JsonProperty("user_first_name") String userFirstName,
    @JsonProperty("user_last_name") String userLastName,
    @JsonProperty("role") String role,
    @JsonProperty("status") String status,
    @JsonProperty("created_at") String createdAt,
    @JsonProperty("updated_at") String updatedAt
) {
}
