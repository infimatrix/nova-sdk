// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * SenderRequest model.
 *
 * @param name JSON property name. Optional.
 * @param email JSON property email.
 * @param isDefault JSON property is_default. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record SenderRequest(
    @JsonProperty("name") String name,
    @JsonProperty("email") String email,
    @JsonProperty("is_default") Boolean isDefault
) {

    /** Returns a new builder for {@link SenderRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link SenderRequest}. */
    public static final class Builder {
        private String name;
        private String email;
        private Boolean isDefault;

        private Builder() {
        }

        /** Sets {@code name}. */
        public Builder name(String value) {
            this.name = value;
            return this;
        }

        /** Sets {@code email}. */
        public Builder email(String value) {
            this.email = value;
            return this;
        }

        /** Sets {@code is_default}. */
        public Builder isDefault(Boolean value) {
            this.isDefault = value;
            return this;
        }

        /** Builds the immutable request. */
        public SenderRequest build() {
            return new SenderRequest(name, email, isDefault);
        }
    }
}
