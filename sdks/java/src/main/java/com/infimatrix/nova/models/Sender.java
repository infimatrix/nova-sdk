// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Sender model.
 *
 * @param name JSON property name. Optional.
 * @param email JSON property email.
 * @param isDefault JSON property is_default. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record Sender(
    @JsonProperty("name") String name,
    @JsonProperty("email") String email,
    @JsonProperty("is_default") Boolean isDefault
) {
}
