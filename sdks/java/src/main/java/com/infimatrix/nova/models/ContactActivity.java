// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * ContactActivity model.
 *
 * @param id JSON property id.
 * @param title JSON property title.
 * @param subject JSON property subject.
 * @param status JSON property status.
 * @param timestamp JSON property timestamp.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ContactActivity(
    @JsonProperty("id") String id,
    @JsonProperty("title") String title,
    @JsonProperty("subject") String subject,
    @JsonProperty("status") String status,
    @JsonProperty("timestamp") String timestamp
) {
}
