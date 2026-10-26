// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * WebhookEndpointCreateUpdateRequest model.
 *
 * @param name JSON property name.
 * @param url JSON property url.
 * @param events JSON property events. Optional.
 * @param isActive JSON property is_active. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record WebhookEndpointCreateUpdateRequest(
    @JsonProperty("name") String name,
    @JsonProperty("url") String url,
    @JsonProperty("events") List<String> events,
    @JsonProperty("is_active") Boolean isActive
) {

    /** Returns a new builder for {@link WebhookEndpointCreateUpdateRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link WebhookEndpointCreateUpdateRequest}. */
    public static final class Builder {
        private String name;
        private String url;
        private List<String> events;
        private Boolean isActive;

        private Builder() {
        }

        /** Sets {@code name}. */
        public Builder name(String value) {
            this.name = value;
            return this;
        }

        /** Sets {@code url}. */
        public Builder url(String value) {
            this.url = value;
            return this;
        }

        /** Sets {@code events}. */
        public Builder events(List<String> value) {
            this.events = value;
            return this;
        }

        /** Sets {@code is_active}. */
        public Builder isActive(Boolean value) {
            this.isActive = value;
            return this;
        }

        /** Builds the immutable request. */
        public WebhookEndpointCreateUpdateRequest build() {
            return new WebhookEndpointCreateUpdateRequest(name, url, events, isActive);
        }
    }
}
