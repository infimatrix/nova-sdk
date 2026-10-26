// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Serializer for checking validity of a password reset token before form submission.
 *
 * @param uid JSON property uid. Optional.
 * @param uidb64 JSON property uidb64. Optional.
 * @param token JSON property token.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ValidateResetTokenRequest(
    @JsonProperty("uid") String uid,
    @JsonProperty("uidb64") String uidb64,
    @JsonProperty("token") String token
) {

    /** Returns a new builder for {@link ValidateResetTokenRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link ValidateResetTokenRequest}. */
    public static final class Builder {
        private String uid;
        private String uidb64;
        private String token;

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

        /** Builds the immutable request. */
        public ValidateResetTokenRequest build() {
            return new ValidateResetTokenRequest(uid, uidb64, token);
        }
    }
}
