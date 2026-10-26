// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * ValidateResetTokenResponse model.
 *
 * @param valid JSON property valid.
 * @param detail JSON property detail.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ValidateResetTokenResponse(
    @JsonProperty("valid") Boolean valid,
    @JsonProperty("detail") String detail
) {
}
