// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * ProviderConfiguration model.
 *
 * @param id JSON property id.
 * @param name JSON property name.
 * @param providerType JSON property provider_type. Optional.
 * @param senders JSON property senders. Optional.
 * @param smtpHost JSON property smtp_host. Optional.
 * @param smtpPort JSON property smtp_port. Optional.
 * @param tlsEnabled JSON property tls_enabled. Optional.
 * @param authenticationType JSON property authentication_type. Optional.
 * @param smtpUser JSON property smtp_user. Optional.
 * @param hasPassword JSON property has_password.
 * @param awsRegion AWS Region e.g. US East (N. Virginia) - us-east-1 Optional.
 * @param awsAccessKeyId AWS Access Key ID Optional.
 * @param hasSecretKey JSON property has_secret_key.
 * @param rateLimitPerMinute Rate limit for marketing emails per minute Optional.
 * @param isActive JSON property is_active. Optional.
 * @param priority Priority routing order (lower is higher priority) Optional.
 * @param createdAt JSON property created_at.
 * @param updatedAt JSON property updated_at.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ProviderConfiguration(
    @JsonProperty("id") String id,
    @JsonProperty("name") String name,
    @JsonProperty("provider_type") String providerType,
    @JsonProperty("senders") List<Sender> senders,
    @JsonProperty("smtp_host") String smtpHost,
    @JsonProperty("smtp_port") Long smtpPort,
    @JsonProperty("tls_enabled") Boolean tlsEnabled,
    @JsonProperty("authentication_type") String authenticationType,
    @JsonProperty("smtp_user") String smtpUser,
    @JsonProperty("has_password") Boolean hasPassword,
    @JsonProperty("aws_region") String awsRegion,
    @JsonProperty("aws_access_key_id") String awsAccessKeyId,
    @JsonProperty("has_secret_key") Boolean hasSecretKey,
    @JsonProperty("rate_limit_per_minute") Long rateLimitPerMinute,
    @JsonProperty("is_active") Boolean isActive,
    @JsonProperty("priority") Long priority,
    @JsonProperty("created_at") String createdAt,
    @JsonProperty("updated_at") String updatedAt
) {
}
