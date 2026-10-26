// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * UserRegisterRequest model.
 *
 * @param email JSON property email.
 * @param password JSON property password.
 * @param firstName JSON property first_name. Optional.
 * @param lastName JSON property last_name. Optional.
 * @param username JSON property username. Optional.
 * @param organizationName JSON property organization_name. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record UserRegisterRequest(
    @JsonProperty("email") String email,
    @JsonProperty("password") String password,
    @JsonProperty("first_name") String firstName,
    @JsonProperty("last_name") String lastName,
    @JsonProperty("username") String username,
    @JsonProperty("organization_name") String organizationName
) {

    /** Returns a new builder for {@link UserRegisterRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link UserRegisterRequest}. */
    public static final class Builder {
        private String email;
        private String password;
        private String firstName;
        private String lastName;
        private String username;
        private String organizationName;

        private Builder() {
        }

        /** Sets {@code email}. */
        public Builder email(String value) {
            this.email = value;
            return this;
        }

        /** Sets {@code password}. */
        public Builder password(String value) {
            this.password = value;
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

        /** Sets {@code username}. */
        public Builder username(String value) {
            this.username = value;
            return this;
        }

        /** Sets {@code organization_name}. */
        public Builder organizationName(String value) {
            this.organizationName = value;
            return this;
        }

        /** Builds the immutable request. */
        public UserRegisterRequest build() {
            return new UserRegisterRequest(email, password, firstName, lastName, username, organizationName);
        }
    }
}
