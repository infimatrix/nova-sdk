// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.Map;

/**
 * TemplateRenderRequest model.
 *
 * @param variables Variable key-values to render template Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record TemplateRenderRequest(
    @JsonProperty("variables") Map<String, Object> variables
) {

    /** Returns a new builder for {@link TemplateRenderRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link TemplateRenderRequest}. */
    public static final class Builder {
        private Map<String, Object> variables;

        private Builder() {
        }

        /** Sets {@code variables}. */
        public Builder variables(Map<String, Object> value) {
            this.variables = value;
            return this;
        }

        /** Builds the immutable request. */
        public TemplateRenderRequest build() {
            return new TemplateRenderRequest(variables);
        }
    }
}
