// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * ContactSummary model.
 *
 * @param id JSON property id.
 * @param userId JSON property user_id.
 * @param contactIdStr User ID (e.g. USR001) Optional.
 * @param username JSON property username. Optional.
 * @param email JSON property email.
 * @param firstName JSON property first_name. Optional.
 * @param lastName JSON property last_name. Optional.
 * @param countryCode Country calling code (e.g., +91, +1) Optional.
 * @param phoneNumber Mobile / Phone number without country code Optional.
 * @param mobileNumber JSON property mobile_number.
 * @param timezone JSON property timezone. Optional.
 * @param status JSON property status. Optional.
 * @param createdAt JSON property created_at.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ContactSummary(
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
    @JsonProperty("created_at") String createdAt
) {
}
