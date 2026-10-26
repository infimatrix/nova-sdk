// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * SendEmailRequest model.
 *
 * @param recipientEmail JSON property recipient_email.
 * @param recipientName JSON property recipient_name. Optional.
 * @param senderName JSON property sender_name. Optional.
 * @param senderEmail JSON property sender_email. Optional.
 * @param subject JSON property subject.
 * @param htmlContent JSON property html_content. Optional.
 * @param textContent JSON property text_content. Optional.
 * @param templateId JSON property template_id. Optional.
 * @param templateName JSON property template_name. Optional.
 * @param note JSON property note. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record SendEmailRequest(
    @JsonProperty("recipient_email") String recipientEmail,
    @JsonProperty("recipient_name") String recipientName,
    @JsonProperty("sender_name") String senderName,
    @JsonProperty("sender_email") String senderEmail,
    @JsonProperty("subject") String subject,
    @JsonProperty("html_content") String htmlContent,
    @JsonProperty("text_content") String textContent,
    @JsonProperty("template_id") String templateId,
    @JsonProperty("template_name") String templateName,
    @JsonProperty("note") String note
) {

    /** Returns a new builder for {@link SendEmailRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link SendEmailRequest}. */
    public static final class Builder {
        private String recipientEmail;
        private String recipientName;
        private String senderName;
        private String senderEmail;
        private String subject;
        private String htmlContent;
        private String textContent;
        private String templateId;
        private String templateName;
        private String note;

        private Builder() {
        }

        /** Sets {@code recipient_email}. */
        public Builder recipientEmail(String value) {
            this.recipientEmail = value;
            return this;
        }

        /** Sets {@code recipient_name}. */
        public Builder recipientName(String value) {
            this.recipientName = value;
            return this;
        }

        /** Sets {@code sender_name}. */
        public Builder senderName(String value) {
            this.senderName = value;
            return this;
        }

        /** Sets {@code sender_email}. */
        public Builder senderEmail(String value) {
            this.senderEmail = value;
            return this;
        }

        /** Sets {@code subject}. */
        public Builder subject(String value) {
            this.subject = value;
            return this;
        }

        /** Sets {@code html_content}. */
        public Builder htmlContent(String value) {
            this.htmlContent = value;
            return this;
        }

        /** Sets {@code text_content}. */
        public Builder textContent(String value) {
            this.textContent = value;
            return this;
        }

        /** Sets {@code template_id}. */
        public Builder templateId(String value) {
            this.templateId = value;
            return this;
        }

        /** Sets {@code template_name}. */
        public Builder templateName(String value) {
            this.templateName = value;
            return this;
        }

        /** Sets {@code note}. */
        public Builder note(String value) {
            this.note = value;
            return this;
        }

        /** Builds the immutable request. */
        public SendEmailRequest build() {
            return new SendEmailRequest(recipientEmail, recipientName, senderName, senderEmail, subject, htmlContent, textContent, templateId, templateName, note);
        }
    }
}
