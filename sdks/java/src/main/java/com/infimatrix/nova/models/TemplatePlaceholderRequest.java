// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * TemplatePlaceholderRequest model.
 *
 * @param name JSON property name.
 * @param defaultValue JSON property default_value. Optional.
 * @param isRequired JSON property is_required. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record TemplatePlaceholderRequest(
    @JsonProperty("name") String name,
    @JsonProperty("default_value") String defaultValue,
    @JsonProperty("is_required") Boolean isRequired
) {

    /** Returns a new builder for {@link TemplatePlaceholderRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link TemplatePlaceholderRequest}. */
    public static final class Builder {
        private String name;
        private String defaultValue;
        private Boolean isRequired;

        private Builder() {
        }

        /** Sets {@code name}. */
        public Builder name(String value) {
            this.name = value;
            return this;
        }

        /** Sets {@code default_value}. */
        public Builder defaultValue(String value) {
            this.defaultValue = value;
            return this;
        }

        /** Sets {@code is_required}. */
        public Builder isRequired(Boolean value) {
            this.isRequired = value;
            return this;
        }

        /** Builds the immutable request. */
        public TemplatePlaceholderRequest build() {
            return new TemplatePlaceholderRequest(name, defaultValue, isRequired);
        }
    }
}
