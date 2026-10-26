// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * User model.
 *
 * @param id JSON property id.
 * @param email JSON property email.
 * @param username Required. 150 characters or fewer. Letters, digits and &#64;/./+/-/_ only.
 * @param firstName JSON property first_name. Optional.
 * @param lastName JSON property last_name. Optional.
 * @param isActive Designates whether this user should be treated as active. Unselect this instead of deleting accounts. Optional.
 * @param isStaff Designates whether the user can log into this admin site.
 * @param isSuperuser Designates that this user has all permissions without explicitly assigning them.
 * @param createdAt JSON property created_at.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record User(
    @JsonProperty("id") String id,
    @JsonProperty("email") String email,
    @JsonProperty("username") String username,
    @JsonProperty("first_name") String firstName,
    @JsonProperty("last_name") String lastName,
    @JsonProperty("is_active") Boolean isActive,
    @JsonProperty("is_staff") Boolean isStaff,
    @JsonProperty("is_superuser") Boolean isSuperuser,
    @JsonProperty("created_at") String createdAt
) {
}
