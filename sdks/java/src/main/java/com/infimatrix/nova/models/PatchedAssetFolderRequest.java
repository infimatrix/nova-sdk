// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * PatchedAssetFolderRequest model.
 *
 * @param name JSON property name. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record PatchedAssetFolderRequest(
    @JsonProperty("name") String name
) {

    /** Returns a new builder for {@link PatchedAssetFolderRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link PatchedAssetFolderRequest}. */
    public static final class Builder {
        private String name;

        private Builder() {
        }

        /** Sets {@code name}. */
        public Builder name(String value) {
            this.name = value;
            return this;
        }

        /** Builds the immutable request. */
        public PatchedAssetFolderRequest build() {
            return new PatchedAssetFolderRequest(name);
        }
    }
}
