// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * TemplatePlaceholder model.
 *
 * @param id JSON property id.
 * @param name JSON property name.
 * @param defaultValue JSON property default_value. Optional.
 * @param isRequired JSON property is_required. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record TemplatePlaceholder(
    @JsonProperty("id") Long id,
    @JsonProperty("name") String name,
    @JsonProperty("default_value") String defaultValue,
    @JsonProperty("is_required") Boolean isRequired
) {
}
