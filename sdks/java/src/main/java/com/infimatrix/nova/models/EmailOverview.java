// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * EmailOverview model.
 *
 * @param totalEmail JSON property total_email.
 * @param sent JSON property sent.
 * @param delivered JSON property delivered.
 * @param opened JSON property opened.
 * @param clicked JSON property clicked.
 * @param bounced JSON property bounced.
 * @param complaint JSON property complaint.
 * @param failed JSON property failed.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record EmailOverview(
    @JsonProperty("total_email") Long totalEmail,
    @JsonProperty("sent") Long sent,
    @JsonProperty("delivered") Long delivered,
    @JsonProperty("opened") Long opened,
    @JsonProperty("clicked") Long clicked,
    @JsonProperty("bounced") Long bounced,
    @JsonProperty("complaint") Long complaint,
    @JsonProperty("failed") Long failed
) {
}
