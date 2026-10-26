// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * LoginRequest model.
 *
 * @param email JSON property email.
 * @param password JSON property password.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record LoginRequest(
    @JsonProperty("email") String email,
    @JsonProperty("password") String password
) {

    /** Returns a new builder for {@link LoginRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link LoginRequest}. */
    public static final class Builder {
        private String email;
        private String password;

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

        /** Builds the immutable request. */
        public LoginRequest build() {
            return new LoginRequest(email, password);
        }
    }
}
