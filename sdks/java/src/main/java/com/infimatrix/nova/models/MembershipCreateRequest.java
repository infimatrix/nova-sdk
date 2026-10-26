// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * MembershipCreateRequest model.
 *
 * @param email JSON property email.
 * @param role JSON property role. Optional.
 * @param status JSON property status. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record MembershipCreateRequest(
    @JsonProperty("email") String email,
    @JsonProperty("role") String role,
    @JsonProperty("status") String status
) {

    /** Returns a new builder for {@link MembershipCreateRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link MembershipCreateRequest}. */
    public static final class Builder {
        private String email;
        private String role;
        private String status;

        private Builder() {
        }

        /** Sets {@code email}. */
        public Builder email(String value) {
            this.email = value;
            return this;
        }

        /** Sets {@code role}. */
        public Builder role(String value) {
            this.role = value;
            return this;
        }

        /** Sets {@code status}. */
        public Builder status(String value) {
            this.status = value;
            return this;
        }

        /** Builds the immutable request. */
        public MembershipCreateRequest build() {
            return new MembershipCreateRequest(email, role, status);
        }
    }
}
