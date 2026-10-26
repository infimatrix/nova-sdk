// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * TemplateRequest model.
 *
 * @param name JSON property name.
 * @param subject JSON property subject. Optional.
 * @param description JSON property description. Optional.
 * @param status JSON property status. Optional.
 * @param actionTypes Action categories e.g. Onboarding Optional.
 * @param designConfig Color and design settings for the template Optional.
 * @param htmlContent JSON property html_content. Optional.
 * @param textContent JSON property text_content. Optional.
 * @param placeholders JSON property placeholders. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record TemplateRequest(
    @JsonProperty("name") String name,
    @JsonProperty("subject") String subject,
    @JsonProperty("description") String description,
    @JsonProperty("status") String status,
    @JsonProperty("action_types") Object actionTypes,
    @JsonProperty("design_config") Object designConfig,
    @JsonProperty("html_content") String htmlContent,
    @JsonProperty("text_content") String textContent,
    @JsonProperty("placeholders") List<TemplatePlaceholderRequest> placeholders
) {

    /** Returns a new builder for {@link TemplateRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link TemplateRequest}. */
    public static final class Builder {
        private String name;
        private String subject;
        private String description;
        private String status;
        private Object actionTypes;
        private Object designConfig;
        private String htmlContent;
        private String textContent;
        private List<TemplatePlaceholderRequest> placeholders;

        private Builder() {
        }

        /** Sets {@code name}. */
        public Builder name(String value) {
            this.name = value;
            return this;
        }

        /** Sets {@code subject}. */
        public Builder subject(String value) {
            this.subject = value;
            return this;
        }

        /** Sets {@code description}. */
        public Builder description(String value) {
            this.description = value;
            return this;
        }

        /** Sets {@code status}. */
        public Builder status(String value) {
            this.status = value;
            return this;
        }

        /** Sets {@code action_types}. */
        public Builder actionTypes(Object value) {
            this.actionTypes = value;
            return this;
        }

        /** Sets {@code design_config}. */
        public Builder designConfig(Object value) {
            this.designConfig = value;
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

        /** Sets {@code placeholders}. */
        public Builder placeholders(List<TemplatePlaceholderRequest> value) {
            this.placeholders = value;
            return this;
        }

        /** Builds the immutable request. */
        public TemplateRequest build() {
            return new TemplateRequest(name, subject, description, status, actionTypes, designConfig, htmlContent, textContent, placeholders);
        }
    }
}
