// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * PatchedTransactionalNotificationRequest model.
 *
 * @param name JSON property name. Optional.
 * @param apiIdentifier Unique API identifier key (e.g. welcome_email) Optional.
 * @param templateId JSON property template_id. Optional.
 * @param description Description of when this notification is triggered Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record PatchedTransactionalNotificationRequest(
    @JsonProperty("name") String name,
    @JsonProperty("api_identifier") String apiIdentifier,
    @JsonProperty("template_id") String templateId,
    @JsonProperty("description") String description
) {

    /** Returns a new builder for {@link PatchedTransactionalNotificationRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link PatchedTransactionalNotificationRequest}. */
    public static final class Builder {
        private String name;
        private String apiIdentifier;
        private String templateId;
        private String description;

        private Builder() {
        }

        /** Sets {@code name}. */
        public Builder name(String value) {
            this.name = value;
            return this;
        }

        /** Sets {@code api_identifier}. */
        public Builder apiIdentifier(String value) {
            this.apiIdentifier = value;
            return this;
        }

        /** Sets {@code template_id}. */
        public Builder templateId(String value) {
            this.templateId = value;
            return this;
        }

        /** Sets {@code description}. */
        public Builder description(String value) {
            this.description = value;
            return this;
        }

        /** Builds the immutable request. */
        public PatchedTransactionalNotificationRequest build() {
            return new PatchedTransactionalNotificationRequest(name, apiIdentifier, templateId, description);
        }
    }
}
