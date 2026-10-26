// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * HealthStatus model.
 *
 * @param status Always `ok`.
 * @param database `healthy` when the database responds.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record HealthStatus(
    @JsonProperty("status") String status,
    @JsonProperty("database") String database
) {
}
