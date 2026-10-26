// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * ContactRequest model.
 *
 * @param userId JSON property user_id. Optional.
 * @param contactIdStr User ID (e.g. USR001) Optional.
 * @param username JSON property username. Optional.
 * @param email JSON property email.
 * @param firstName JSON property first_name. Optional.
 * @param lastName JSON property last_name. Optional.
 * @param countryCode JSON property country_code. Optional.
 * @param phoneNumber JSON property phone_number. Optional.
 * @param timezone JSON property timezone. Optional.
 * @param status JSON property status. Optional.
 * @param metadata JSON property metadata. Optional.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record ContactRequest(
    @JsonProperty("user_id") String userId,
    @JsonProperty("contact_id_str") String contactIdStr,
    @JsonProperty("username") String username,
    @JsonProperty("email") String email,
    @JsonProperty("first_name") String firstName,
    @JsonProperty("last_name") String lastName,
    @JsonProperty("country_code") String countryCode,
    @JsonProperty("phone_number") String phoneNumber,
    @JsonProperty("timezone") String timezone,
    @JsonProperty("status") String status,
    @JsonProperty("metadata") Object metadata
) {

    /** Returns a new builder for {@link ContactRequest}. */
    public static Builder builder() {
        return new Builder();
    }

    /** Fluent builder for {@link ContactRequest}. */
    public static final class Builder {
        private String userId;
        private String contactIdStr;
        private String username;
        private String email;
        private String firstName;
        private String lastName;
        private String countryCode;
        private String phoneNumber;
        private String timezone;
        private String status;
        private Object metadata;

        private Builder() {
        }

        /** Sets {@code user_id}. */
        public Builder userId(String value) {
            this.userId = value;
            return this;
        }

        /** Sets {@code contact_id_str}. */
        public Builder contactIdStr(String value) {
            this.contactIdStr = value;
            return this;
        }

        /** Sets {@code username}. */
        public Builder username(String value) {
            this.username = value;
            return this;
        }

        /** Sets {@code email}. */
        public Builder email(String value) {
            this.email = value;
            return this;
        }

        /** Sets {@code first_name}. */
        public Builder firstName(String value) {
            this.firstName = value;
            return this;
        }

        /** Sets {@code last_name}. */
        public Builder lastName(String value) {
            this.lastName = value;
            return this;
        }

        /** Sets {@code country_code}. */
        public Builder countryCode(String value) {
            this.countryCode = value;
            return this;
        }

        /** Sets {@code phone_number}. */
        public Builder phoneNumber(String value) {
            this.phoneNumber = value;
            return this;
        }

        /** Sets {@code timezone}. */
        public Builder timezone(String value) {
            this.timezone = value;
            return this;
        }

        /** Sets {@code status}. */
        public Builder status(String value) {
            this.status = value;
            return this;
        }

        /** Sets {@code metadata}. */
        public Builder metadata(Object value) {
            this.metadata = value;
            return this;
        }

        /** Builds the immutable request. */
        public ContactRequest build() {
            return new ContactRequest(userId, contactIdStr, username, email, firstName, lastName, countryCode, phoneNumber, timezone, status, metadata);
        }
    }
}
