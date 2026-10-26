// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Serializer for requesting a password reset email instructions.
 *
 * @param email JSON property email.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ForgotPasswordRequest(
    @JsonProperty("email") String email
) {

    /** Returns a new builder for {@link ForgotPasswordRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link ForgotPasswordRequest}. */
    public static final class Builder {
        private String email;

        private Builder() {
        }

        /** Sets {@code email}. */
        public Builder email(String value) {
            this.email = value;
            return this;
        }

        /** Builds the immutable request. */
        public ForgotPasswordRequest build() {
            return new ForgotPasswordRequest(email);
        }
    }
}
