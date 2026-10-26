// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * TestWebhookRequest model.
 *
 * @param eventType JSON property event_type. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record TestWebhookRequest(
    @JsonProperty("event_type") String eventType
) {

    /** Returns a new builder for {@link TestWebhookRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link TestWebhookRequest}. */
    public static final class Builder {
        private String eventType;

        private Builder() {
        }

        /** Sets {@code event_type}. */
        public Builder eventType(String value) {
            this.eventType = value;
            return this;
        }

        /** Builds the immutable request. */
        public TestWebhookRequest build() {
            return new TestWebhookRequest(eventType);
        }
    }
}
