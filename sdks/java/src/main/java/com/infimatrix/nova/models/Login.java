// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.
// Do not edit by hand; run the script to regenerate.

package com.infimatrix.nova.models;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

/**
 * Login model.
 *
 * @param access JSON property access.
 * @param refresh JSON property refresh.
 * @param user JSON property user.
 * @param tenants JSON property tenants.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
@JsonInclude(JsonInclude.Include.NON_NULL)
public record Login(
    @JsonProperty("access") String access,
    @JsonProperty("refresh") String refresh,
    @JsonProperty("user") User user,
    @JsonProperty("tenants") List<TenantMembershipSummary> tenants
) {
}
