// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Serializer for changing current password for authenticated users.
 *
 * @param oldPassword JSON property old_password.
 * @param newPassword JSON property new_password.
 * @param confirmPassword JSON property confirm_password.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ChangePasswordRequest(
    @JsonProperty("old_password") String oldPassword,
    @JsonProperty("new_password") String newPassword,
    @JsonProperty("confirm_password") String confirmPassword
) {

    /** Returns a new builder for {@link ChangePasswordRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link ChangePasswordRequest}. */
    public static final class Builder {
        private String oldPassword;
        private String newPassword;
        private String confirmPassword;

        private Builder() {
        }

        /** Sets {@code old_password}. */
        public Builder oldPassword(String value) {
            this.oldPassword = value;
            return this;
        }

        /** Sets {@code new_password}. */
        public Builder newPassword(String value) {
            this.newPassword = value;
            return this;
        }

        /** Sets {@code confirm_password}. */
        public Builder confirmPassword(String value) {
            this.confirmPassword = value;
            return this;
        }

        /** Builds the immutable request. */
        public ChangePasswordRequest build() {
            return new ChangePasswordRequest(oldPassword, newPassword, confirmPassword);
        }
    }
}
