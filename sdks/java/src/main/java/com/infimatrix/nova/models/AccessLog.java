// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * Read-only serializer for access log entries.
 *
 * @param id JSON property id.
 * @param workspaceName JSON property workspace_name.
 * @param user JSON property user.
 * @param userEmail JSON property user_email.
 * @param userName JSON property user_name.
 * @param createdBy JSON property created_by.
 * @param clientCode JSON property client_code.
 * @param category JSON property category.
 * @param categoryDisplay JSON property category_display.
 * @param action Human-readable action label, e.g. 'User Login', 'Uploaded Asset'.
 * @param description Optional detailed description of the activity.
 * @param httpMethod JSON property http_method.
 * @param path JSON property path.
 * @param queryString JSON property query_string.
 * @param statusCode JSON property status_code.
 * @param ipAddress JSON property ip_address.
 * @param userAgent JSON property user_agent.
 * @param resourceType Type of resource, e.g. 'MediaAsset', 'Contact', 'Template'.
 * @param resourceId Primary key of the resource acted upon.
 * @param responseTimeMs Response time in milliseconds.
 * @param metadata Additional structured context about the activity.
 * @param createdAt JSON property created_at.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record AccessLog(
    @JsonProperty("id") String id,
    @JsonProperty("workspace_name") String workspaceName,
    @JsonProperty("user") String user,
    @JsonProperty("user_email") String userEmail,
    @JsonProperty("user_name") String userName,
    @JsonProperty("created_by") String createdBy,
    @JsonProperty("client_code") String clientCode,
    @JsonProperty("category") String category,
    @JsonProperty("category_display") String categoryDisplay,
    @JsonProperty("action") String action,
    @JsonProperty("description") String description,
    @JsonProperty("http_method") String httpMethod,
    @JsonProperty("path") String path,
    @JsonProperty("query_string") String queryString,
    @JsonProperty("status_code") Long statusCode,
    @JsonProperty("ip_address") String ipAddress,
    @JsonProperty("user_agent") String userAgent,
    @JsonProperty("resource_type") String resourceType,
    @JsonProperty("resource_id") String resourceId,
    @JsonProperty("response_time_ms") Long responseTimeMs,
    @JsonProperty("metadata") Object metadata,
    @JsonProperty("created_at") String createdAt
) {
}
