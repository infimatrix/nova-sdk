// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Serializer for creating a new API Key for the authenticated user.
 *
 * @param name JSON property name. Optional.
 * @param expiresAt JSON property expires_at. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record APIKeyCreateRequest(
    @JsonProperty("name") String name,
    @JsonProperty("expires_at") String expiresAt
) {

    /** Returns a new builder for {@link APIKeyCreateRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link APIKeyCreateRequest}. */
    public static final class Builder {
        private String name;
        private String expiresAt;

        private Builder() {
        }

        /** Sets {@code name}. */
        public Builder name(String value) {
            this.name = value;
            return this;
        }

        /** Sets {@code expires_at}. */
        public Builder expiresAt(String value) {
            this.expiresAt = value;
            return this;
        }

        /** Builds the immutable request. */
        public APIKeyCreateRequest build() {
            return new APIKeyCreateRequest(name, expiresAt);
        }
    }
}
