// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * Template model.
 *
 * @param id JSON property id.
 * @param name JSON property name.
 * @param slug JSON property slug.
 * @param subject JSON property subject. Optional.
 * @param description JSON property description. Optional.
 * @param status JSON property status. Optional.
 * @param actionTypes Action categories e.g. Onboarding Optional.
 * @param designConfig Color and design settings for the template Optional.
 * @param htmlContent JSON property html_content. Optional.
 * @param textContent JSON property text_content. Optional.
 * @param placeholders JSON property placeholders. Optional.
 * @param createdAt JSON property created_at.
 * @param updatedAt JSON property updated_at.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record Template(
    @JsonProperty("id") String id,
    @JsonProperty("name") String name,
    @JsonProperty("slug") String slug,
    @JsonProperty("subject") String subject,
    @JsonProperty("description") String description,
    @JsonProperty("status") String status,
    @JsonProperty("action_types") Object actionTypes,
    @JsonProperty("design_config") Object designConfig,
    @JsonProperty("html_content") String htmlContent,
    @JsonProperty("text_content") String textContent,
    @JsonProperty("placeholders") List<TemplatePlaceholder> placeholders,
    @JsonProperty("created_at") String createdAt,
    @JsonProperty("updated_at") String updatedAt
) {
}
