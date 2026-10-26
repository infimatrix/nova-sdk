// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * BulkContactDeleteResult model.
 *
 * @param success JSON property success.
 * @param deletedCount JSON property deleted_count.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record BulkContactDeleteResult(
    @JsonProperty("success") Boolean success,
    @JsonProperty("deleted_count") Long deletedCount
) {
}
