// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * ProviderTypeInfo model.
 *
 * @param key JSON property key.
 * @param label JSON property label.
 * @param description JSON property description.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ProviderTypeInfo(
    @JsonProperty("key") String key,
    @JsonProperty("label") String label,
    @JsonProperty("description") String description
) {
}
