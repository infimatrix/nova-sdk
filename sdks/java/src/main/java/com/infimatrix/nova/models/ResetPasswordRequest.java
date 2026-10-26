// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Serializer for confirming password reset via single-use reset token.
 *
 * @param uid JSON property uid. Optional.
 * @param uidb64 JSON property uidb64. Optional.
 * @param token JSON property token.
 * @param newPassword JSON property new_password.
 * @param confirmPassword JSON property confirm_password. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ResetPasswordRequest(
    @JsonProperty("uid") String uid,
    @JsonProperty("uidb64") String uidb64,
    @JsonProperty("token") String token,
    @JsonProperty("new_password") String newPassword,
    @JsonProperty("confirm_password") String confirmPassword
) {

    /** Returns a new builder for {@link ResetPasswordRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link ResetPasswordRequest}. */
    public static final class Builder {
        private String uid;
        private String uidb64;
        private String token;
        private String newPassword;
        private String confirmPassword;

        private Builder() {
        }

        /** Sets {@code uid}. */
        public Builder uid(String value) {
            this.uid = value;
            return this;
        }

        /** Sets {@code uidb64}. */
        public Builder uidb64(String value) {
            this.uidb64 = value;
            return this;
        }

        /** Sets {@code token}. */
        public Builder token(String value) {
            this.token = value;
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
        public ResetPasswordRequest build() {
            return new ResetPasswordRequest(uid, uidb64, token, newPassword, confirmPassword);
        }
    }
}
