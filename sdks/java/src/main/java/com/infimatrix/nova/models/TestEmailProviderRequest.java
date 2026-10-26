// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * TestEmailProviderRequest model.
 *
 * @param recipientEmail Recipient email address to receive the test email
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record TestEmailProviderRequest(
    @JsonProperty("recipient_email") String recipientEmail
) {

    /** Returns a new builder for {@link TestEmailProviderRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link TestEmailProviderRequest}. */
    public static final class Builder {
        private String recipientEmail;

        private Builder() {
        }

        /** Sets {@code recipient_email}. */
        public Builder recipientEmail(String value) {
            this.recipientEmail = value;
            return this;
        }

        /** Builds the immutable request. */
        public TestEmailProviderRequest build() {
            return new TestEmailProviderRequest(recipientEmail);
        }
    }
}
