// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;

/**
 * TransactionalTestDispatch model.
 *
 * @param message JSON property message.
 * @param messageId JSON property message_id.
 * @param emailId JSON property email_id.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record TransactionalTestDispatch(
    @JsonProperty("message") String message,
    @JsonProperty("message_id") String messageId,
    @JsonProperty("email_id") String emailId
) {
}
