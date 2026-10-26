// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * UserRequest model.
 *
 * @param email JSON property email.
 * @param username Required. 150 characters or fewer. Letters, digits and &#64;/./+/-/_ only.
 * @param firstName JSON property first_name. Optional.
 * @param lastName JSON property last_name. Optional.
 * @param isActive Designates whether this user should be treated as active. Unselect this instead of deleting accounts. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record UserRequest(
    @JsonProperty("email") String email,
    @JsonProperty("username") String username,
    @JsonProperty("first_name") String firstName,
    @JsonProperty("last_name") String lastName,
    @JsonProperty("is_active") Boolean isActive
) {

    /** Returns a new builder for {@link UserRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link UserRequest}. */
    public static final class Builder {
        private String email;
        private String username;
        private String firstName;
        private String lastName;
        private Boolean isActive;

        private Builder() {
        }

        /** Sets {@code email}. */
        public Builder email(String value) {
            this.email = value;
            return this;
        }

        /** Sets {@code username}. */
        public Builder username(String value) {
            this.username = value;
            return this;
        }

        /** Sets {@code first_name}. */
        public Builder firstName(String value) {
            this.firstName = value;
            return this;
        }

        /** Sets {@code last_name}. */
        public Builder lastName(String value) {
            this.lastName = value;
            return this;
        }

        /** Sets {@code is_active}. */
        public Builder isActive(Boolean value) {
            this.isActive = value;
            return this;
        }

        /** Builds the immutable request. */
        public UserRequest build() {
            return new UserRequest(email, username, firstName, lastName, isActive);
        }
    }
}
