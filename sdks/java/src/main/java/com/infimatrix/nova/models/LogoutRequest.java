// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * LogoutRequest model.
 *
 * @param refresh JSON property refresh.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record LogoutRequest(
    @JsonProperty("refresh") String refresh
) {

    /** Returns a new builder for {@link LogoutRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link LogoutRequest}. */
    public static final class Builder {
        private String refresh;

        private Builder() {
        }

        /** Sets {@code refresh}. */
        public Builder refresh(String value) {
            this.refresh = value;
            return this;
        }

        /** Builds the immutable request. */
        public LogoutRequest build() {
            return new LogoutRequest(refresh);
        }
    }
}
