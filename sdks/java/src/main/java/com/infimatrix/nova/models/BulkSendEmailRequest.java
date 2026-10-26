// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import java.util.Map;

/**
 * BulkSendEmailRequest model.
 *
 * @param templateId JSON property template_id.
 * @param contactIds JSON property contact_ids.
 * @param fallbackVariables JSON property fallback_variables. Optional.
 * @param senderEmail JSON property sender_email.
 * @param providerId JSON property provider_id. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record BulkSendEmailRequest(
    @JsonProperty("template_id") String templateId,
    @JsonProperty("contact_ids") List<String> contactIds,
    @JsonProperty("fallback_variables") Map<String, Object> fallbackVariables,
    @JsonProperty("sender_email") String senderEmail,
    @JsonProperty("provider_id") String providerId
) {

    /** Returns a new builder for {@link BulkSendEmailRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link BulkSendEmailRequest}. */
    public static final class Builder {
        private String templateId;
        private List<String> contactIds;
        private Map<String, Object> fallbackVariables;
        private String senderEmail;
        private String providerId;

        private Builder() {
        }

        /** Sets {@code template_id}. */
        public Builder templateId(String value) {
            this.templateId = value;
            return this;
        }

        /** Sets {@code contact_ids}. */
        public Builder contactIds(List<String> value) {
            this.contactIds = value;
            return this;
        }

        /** Sets {@code fallback_variables}. */
        public Builder fallbackVariables(Map<String, Object> value) {
            this.fallbackVariables = value;
            return this;
        }

        /** Sets {@code sender_email}. */
        public Builder senderEmail(String value) {
            this.senderEmail = value;
            return this;
        }

        /** Sets {@code provider_id}. */
        public Builder providerId(String value) {
            this.providerId = value;
            return this;
        }

        /** Builds the immutable request. */
        public BulkSendEmailRequest build() {
            return new BulkSendEmailRequest(templateId, contactIds, fallbackVariables, senderEmail, providerId);
        }
    }
}
