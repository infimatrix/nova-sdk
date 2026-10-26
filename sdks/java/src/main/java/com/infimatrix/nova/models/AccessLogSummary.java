// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Compact serializer for access log list views.
 *
 * @param id JSON property id.
 * @param workspaceName JSON property workspace_name.
 * @param ipAddress JSON property ip_address.
 * @param clientCode JSON property client_code.
 * @param action JSON property action.
 * @param createdBy JSON property created_by.
 * @param createdAt JSON property created_at.
 * @param category JSON property category.
 * @param categoryDisplay JSON property category_display.
 * @param httpMethod JSON property http_method.
 * @param path JSON property path.
 * @param statusCode JSON property status_code.
 * @param responseTimeMs JSON property response_time_ms.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record AccessLogSummary(
    @JsonProperty("id") String id,
    @JsonProperty("workspace_name") String workspaceName,
    @JsonProperty("ip_address") String ipAddress,
    @JsonProperty("client_code") String clientCode,
    @JsonProperty("action") String action,
    @JsonProperty("created_by") String createdBy,
    @JsonProperty("created_at") String createdAt,
    @JsonProperty("category") String category,
    @JsonProperty("category_display") String categoryDisplay,
    @JsonProperty("http_method") String httpMethod,
    @JsonProperty("path") String path,
    @JsonProperty("status_code") Long statusCode,
    @JsonProperty("response_time_ms") Long responseTimeMs
) {
}
