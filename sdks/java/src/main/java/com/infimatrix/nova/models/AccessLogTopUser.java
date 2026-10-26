// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * AccessLogTopUser model.
 *
 * @param userEmail JSON property user__email.
 * @param activityCount JSON property activity_count.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record AccessLogTopUser(
    @JsonProperty("user__email") String userEmail,
    @JsonProperty("activity_count") Long activityCount
) {
}
