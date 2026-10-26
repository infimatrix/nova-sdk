// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * PatchedTenantUpdateRequest model.
 *
 * @param name JSON property name. Optional.
 * @param website Workspace domain / website URL Optional.
 * @param logoUrl Workspace logo / favicon URL Optional.
 * @param status JSON property status. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record PatchedTenantUpdateRequest(
    @JsonProperty("name") String name,
    @JsonProperty("website") String website,
    @JsonProperty("logo_url") String logoUrl,
    @JsonProperty("status") String status
) {

    /** Returns a new builder for {@link PatchedTenantUpdateRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link PatchedTenantUpdateRequest}. */
    public static final class Builder {
        private String name;
        private String website;
        private String logoUrl;
        private String status;

        private Builder() {
        }

        /** Sets {@code name}. */
        public Builder name(String value) {
            this.name = value;
            return this;
        }

        /** Sets {@code website}. */
        public Builder website(String value) {
            this.website = value;
            return this;
        }

        /** Sets {@code logo_url}. */
        public Builder logoUrl(String value) {
            this.logoUrl = value;
            return this;
        }

        /** Sets {@code status}. */
        public Builder status(String value) {
            this.status = value;
            return this;
        }

        /** Builds the immutable request. */
        public PatchedTenantUpdateRequest build() {
            return new PatchedTenantUpdateRequest(name, website, logoUrl, status);
        }
    }
}
