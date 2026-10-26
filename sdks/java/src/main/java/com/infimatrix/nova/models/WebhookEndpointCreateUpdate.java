// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * WebhookEndpointCreateUpdate model.
 *
 * @param id JSON property id.
 * @param name JSON property name.
 * @param url JSON property url.
 * @param events JSON property events. Optional.
 * @param isActive JSON property is_active. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record WebhookEndpointCreateUpdate(
    @JsonProperty("id") String id,
    @JsonProperty("name") String name,
    @JsonProperty("url") String url,
    @JsonProperty("events") List<String> events,
    @JsonProperty("is_active") Boolean isActive
) {
}
