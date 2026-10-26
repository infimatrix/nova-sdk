// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * ProviderConfigurationCreateUpdateRequest model.
 *
 * @param name JSON property name.
 * @param providerType JSON property provider_type. Optional.
 * @param senders JSON property senders. Optional.
 * @param smtpHost JSON property smtp_host. Optional.
 * @param smtpPort JSON property smtp_port. Optional.
 * @param tlsEnabled JSON property tls_enabled. Optional.
 * @param authenticationType JSON property authentication_type. Optional.
 * @param smtpUser JSON property smtp_user. Optional.
 * @param smtpPassword JSON property smtp_password. Optional.
 * @param awsRegion AWS Region e.g. US East (N. Virginia) - us-east-1 Optional.
 * @param awsAccessKeyId AWS Access Key ID Optional.
 * @param awsSecretAccessKey JSON property aws_secret_access_key. Optional.
 * @param rateLimitPerMinute Rate limit for marketing emails per minute Optional.
 * @param isActive JSON property is_active. Optional.
 * @param priority Priority routing order (lower is higher priority) Optional.
 * @param encryptedCredentials Encrypted API keys and secrets Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ProviderConfigurationCreateUpdateRequest(
    @JsonProperty("name") String name,
    @JsonProperty("provider_type") String providerType,
    @JsonProperty("senders") List<SenderRequest> senders,
    @JsonProperty("smtp_host") String smtpHost,
    @JsonProperty("smtp_port") Long smtpPort,
    @JsonProperty("tls_enabled") Boolean tlsEnabled,
    @JsonProperty("authentication_type") String authenticationType,
    @JsonProperty("smtp_user") String smtpUser,
    @JsonProperty("smtp_password") String smtpPassword,
    @JsonProperty("aws_region") String awsRegion,
    @JsonProperty("aws_access_key_id") String awsAccessKeyId,
    @JsonProperty("aws_secret_access_key") String awsSecretAccessKey,
    @JsonProperty("rate_limit_per_minute") Long rateLimitPerMinute,
    @JsonProperty("is_active") Boolean isActive,
    @JsonProperty("priority") Long priority,
    @JsonProperty("encrypted_credentials") Object encryptedCredentials
) {

    /** Returns a new builder for {@link ProviderConfigurationCreateUpdateRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link ProviderConfigurationCreateUpdateRequest}. */
    public static final class Builder {
        private String name;
        private String providerType;
        private List<SenderRequest> senders;
        private String smtpHost;
        private Long smtpPort;
        private Boolean tlsEnabled;
        private String authenticationType;
        private String smtpUser;
        private String smtpPassword;
        private String awsRegion;
        private String awsAccessKeyId;
        private String awsSecretAccessKey;
        private Long rateLimitPerMinute;
        private Boolean isActive;
        private Long priority;
        private Object encryptedCredentials;

        private Builder() {
        }

        /** Sets {@code name}. */
        public Builder name(String value) {
            this.name = value;
            return this;
        }

        /** Sets {@code provider_type}. */
        public Builder providerType(String value) {
            this.providerType = value;
            return this;
        }

        /** Sets {@code senders}. */
        public Builder senders(List<SenderRequest> value) {
            this.senders = value;
            return this;
        }

        /** Sets {@code smtp_host}. */
        public Builder smtpHost(String value) {
            this.smtpHost = value;
            return this;
        }

        /** Sets {@code smtp_port}. */
        public Builder smtpPort(Long value) {
            this.smtpPort = value;
            return this;
        }

        /** Sets {@code tls_enabled}. */
        public Builder tlsEnabled(Boolean value) {
            this.tlsEnabled = value;
            return this;
        }

        /** Sets {@code authentication_type}. */
        public Builder authenticationType(String value) {
            this.authenticationType = value;
            return this;
        }

        /** Sets {@code smtp_user}. */
        public Builder smtpUser(String value) {
            this.smtpUser = value;
            return this;
        }

        /** Sets {@code smtp_password}. */
        public Builder smtpPassword(String value) {
            this.smtpPassword = value;
            return this;
        }

        /** Sets {@code aws_region}. */
        public Builder awsRegion(String value) {
            this.awsRegion = value;
            return this;
        }

        /** Sets {@code aws_access_key_id}. */
        public Builder awsAccessKeyId(String value) {
            this.awsAccessKeyId = value;
            return this;
        }

        /** Sets {@code aws_secret_access_key}. */
        public Builder awsSecretAccessKey(String value) {
            this.awsSecretAccessKey = value;
            return this;
        }

        /** Sets {@code rate_limit_per_minute}. */
        public Builder rateLimitPerMinute(Long value) {
            this.rateLimitPerMinute = value;
            return this;
        }

        /** Sets {@code is_active}. */
        public Builder isActive(Boolean value) {
            this.isActive = value;
            return this;
        }

        /** Sets {@code priority}. */
        public Builder priority(Long value) {
            this.priority = value;
            return this;
        }

        /** Sets {@code encrypted_credentials}. */
        public Builder encryptedCredentials(Object value) {
            this.encryptedCredentials = value;
            return this;
        }

        /** Builds the immutable request. */
        public ProviderConfigurationCreateUpdateRequest build() {
            return new ProviderConfigurationCreateUpdateRequest(name, providerType, senders, smtpHost, smtpPort, tlsEnabled, authenticationType, smtpUser, smtpPassword, awsRegion, awsAccessKeyId, awsSecretAccessKey, rateLimitPerMinute, isActive, priority, encryptedCredentials);
        }
    }
}
