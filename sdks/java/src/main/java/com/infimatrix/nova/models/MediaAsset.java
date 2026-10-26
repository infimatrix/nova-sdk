// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * MediaAsset model.
 *
 * @param id JSON property id.
 * @param folder JSON property folder. Optional.
 * @param folderName JSON property folder_name.
 * @param name JSON property name.
 * @param file JSON property file.
 * @param fileSize File size in bytes
 * @param formattedFileSize JSON property formatted_file_size.
 * @param mimeType JSON property mime_type.
 * @param publicUrl JSON property public_url.
 * @param templateUrl JSON property template_url.
 * @param createdAt JSON property created_at.
 * @param updatedAt JSON property updated_at.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record MediaAsset(
    @JsonProperty("id") String id,
    @JsonProperty("folder") String folder,
    @JsonProperty("folder_name") String folderName,
    @JsonProperty("name") String name,
    @JsonProperty("file") String file,
    @JsonProperty("file_size") Long fileSize,
    @JsonProperty("formatted_file_size") String formattedFileSize,
    @JsonProperty("mime_type") String mimeType,
    @JsonProperty("public_url") String publicUrl,
    @JsonProperty("template_url") String templateUrl,
    @JsonProperty("created_at") String createdAt,
    @JsonProperty("updated_at") String updatedAt
) {
}
