// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * ContactGroup model.
 *
 * @param id JSON property id.
 * @param name JSON property name.
 * @param description JSON property description. Optional.
 * @param contacts JSON property contacts. Optional.
 * @param createdAt JSON property created_at.
 * @param updatedAt JSON property updated_at.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ContactGroup(
    @JsonProperty("id") String id,
    @JsonProperty("name") String name,
    @JsonProperty("description") String description,
    @JsonProperty("contacts") List<String> contacts,
    @JsonProperty("created_at") String createdAt,
    @JsonProperty("updated_at") String updatedAt
) {
}
