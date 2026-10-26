// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Contact model.
 *
 * @param id JSON property id.
 * @param userId JSON property user_id. Optional.
 * @param contactIdStr User ID (e.g. USR001) Optional.
 * @param username JSON property username. Optional.
 * @param email JSON property email.
 * @param firstName JSON property first_name. Optional.
 * @param lastName JSON property last_name. Optional.
 * @param countryCode JSON property country_code. Optional.
 * @param phoneNumber JSON property phone_number. Optional.
 * @param mobileNumber JSON property mobile_number.
 * @param timezone JSON property timezone. Optional.
 * @param status JSON property status. Optional.
 * @param metadata JSON property metadata. Optional.
 * @param createdAt JSON property created_at.
 * @param updatedAt JSON property updated_at.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record Contact(
    @JsonProperty("id") String id,
    @JsonProperty("user_id") String userId,
    @JsonProperty("contact_id_str") String contactIdStr,
    @JsonProperty("username") String username,
    @JsonProperty("email") String email,
    @JsonProperty("first_name") String firstName,
    @JsonProperty("last_name") String lastName,
    @JsonProperty("country_code") String countryCode,
    @JsonProperty("phone_number") String phoneNumber,
    @JsonProperty("mobile_number") String mobileNumber,
    @JsonProperty("timezone") String timezone,
    @JsonProperty("status") String status,
    @JsonProperty("metadata") Object metadata,
    @JsonProperty("created_at") String createdAt,
    @JsonProperty("updated_at") String updatedAt
) {
}
