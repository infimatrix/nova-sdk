// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * BulkContactDeleteRequest model.
 *
 * @param contactIds JSON property contact_ids.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record BulkContactDeleteRequest(
    @JsonProperty("contact_ids") List<String> contactIds
) {

    /** Returns a new builder for {@link BulkContactDeleteRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link BulkContactDeleteRequest}. */
    public static final class Builder {
        private List<String> contactIds;

        private Builder() {
        }

        /** Sets {@code contact_ids}. */
        public Builder contactIds(List<String> value) {
            this.contactIds = value;
            return this;
        }

        /** Builds the immutable request. */
        public BulkContactDeleteRequest build() {
            return new BulkContactDeleteRequest(contactIds);
        }
    }
}
