// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;

/**
 * AccessLogStats model.
 *
 * @param total JSON property total.
 * @param last24h JSON property last_24h.
 * @param last7d JSON property last_7d.
 * @param categoryBreakdown Access-log count keyed by category.
 * @param topUsers JSON property top_users.
 * @param avgResponseTimeMs JSON property avg_response_time_ms.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record AccessLogStats(
    @JsonProperty("total") Long total,
    @JsonProperty("last_24h") Long last24h,
    @JsonProperty("last_7d") Long last7d,
    @JsonProperty("category_breakdown") Map<String, Object> categoryBreakdown,
    @JsonProperty("top_users") List<AccessLogTopUser> topUsers,
    @JsonProperty("avg_response_time_ms") Double avgResponseTimeMs
) {
}
