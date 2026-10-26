// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * PatchedContactGroupRequest model.
 *
 * @param name JSON property name. Optional.
 * @param description JSON property description. Optional.
 * @param contacts JSON property contacts. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record PatchedContactGroupRequest(
    @JsonProperty("name") String name,
    @JsonProperty("description") String description,
    @JsonProperty("contacts") List<String> contacts
) {

    /** Returns a new builder for {@link PatchedContactGroupRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link PatchedContactGroupRequest}. */
    public static final class Builder {
        private String name;
        private String description;
        private List<String> contacts;

        private Builder() {
        }

        /** Sets {@code name}. */
        public Builder name(String value) {
            this.name = value;
            return this;
        }

        /** Sets {@code description}. */
        public Builder description(String value) {
            this.description = value;
            return this;
        }

        /** Sets {@code contacts}. */
        public Builder contacts(List<String> value) {
            this.contacts = value;
            return this;
        }

        /** Builds the immutable request. */
        public PatchedContactGroupRequest build() {
            return new PatchedContactGroupRequest(name, description, contacts);
        }
    }
}
