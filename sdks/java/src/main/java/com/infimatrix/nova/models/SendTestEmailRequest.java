// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * SendTestEmailRequest model.
 *
 * @param providerId JSON property provider_id. Optional.
 * @param senderEmail JSON property sender_email. Optional.
 * @param fromName JSON property from_name. Optional.
 * @param recipientEmail JSON property recipient_email.
 * @param ccEmails JSON property cc_emails. Optional.
 * @param bccEmails JSON property bcc_emails. Optional.
 * @param replyTo JSON property reply_to. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record SendTestEmailRequest(
    @JsonProperty("provider_id") String providerId,
    @JsonProperty("sender_email") String senderEmail,
    @JsonProperty("from_name") String fromName,
    @JsonProperty("recipient_email") String recipientEmail,
    @JsonProperty("cc_emails") String ccEmails,
    @JsonProperty("bcc_emails") String bccEmails,
    @JsonProperty("reply_to") String replyTo
) {

    /** Returns a new builder for {@link SendTestEmailRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link SendTestEmailRequest}. */
    public static final class Builder {
        private String providerId;
        private String senderEmail;
        private String fromName;
        private String recipientEmail;
        private String ccEmails;
        private String bccEmails;
        private String replyTo;

        private Builder() {
        }

        /** Sets {@code provider_id}. */
        public Builder providerId(String value) {
            this.providerId = value;
            return this;
        }

        /** Sets {@code sender_email}. */
        public Builder senderEmail(String value) {
            this.senderEmail = value;
            return this;
        }

        /** Sets {@code from_name}. */
        public Builder fromName(String value) {
            this.fromName = value;
            return this;
        }

        /** Sets {@code recipient_email}. */
        public Builder recipientEmail(String value) {
            this.recipientEmail = value;
            return this;
        }

        /** Sets {@code cc_emails}. */
        public Builder ccEmails(String value) {
            this.ccEmails = value;
            return this;
        }

        /** Sets {@code bcc_emails}. */
        public Builder bccEmails(String value) {
            this.bccEmails = value;
            return this;
        }

        /** Sets {@code reply_to}. */
        public Builder replyTo(String value) {
            this.replyTo = value;
            return this;
        }

        /** Builds the immutable request. */
        public SendTestEmailRequest build() {
            return new SendTestEmailRequest(providerId, senderEmail, fromName, recipientEmail, ccEmails, bccEmails, replyTo);
        }
    }
}
