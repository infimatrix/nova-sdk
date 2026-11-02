package com.infimatrix.nova.resources;

import com.infimatrix.nova.NovaConfig;
import com.infimatrix.nova.errors.NovaClientValidationException;
import com.infimatrix.nova.http.ApiRequest;
import com.infimatrix.nova.http.HttpMethod;
import com.infimatrix.nova.http.HttpTransport;
import com.infimatrix.nova.models.CurrentTenant;
import com.infimatrix.nova.models.UserMe;

/** Small client-side validation helpers shared by the API classes. */
final class Validate {
    private Validate() {
    }

    /** Returns the trimmed value, or throws when it is null or blank. */
    static String nonBlank(String value, String label) {
        if (value == null || value.isBlank()) {
            throw new NovaClientValidationException(label + " must be a non-empty string.");
        }
        return value.strip();
    }

    /** Resolves a tenant id from an explicit argument, per-call options, or the client default. */
    static String tenant(HttpTransport http, String explicit) {
        String tenant = explicit != null ? explicit : http.options().tenantId();
        if (tenant == null) {
            tenant = http.config().tenantId();
        }
        if (tenant == null || tenant.isBlank()) {
            throw new NovaClientValidationException("tenant_id must be provided or configured on the client.");
        }
        return NovaConfig.normalizeTenantId(tenant);
    }

    /**
     * Like {@link #tenant(HttpTransport, String)}, but when no tenant is named anywhere (argument, per-call options,
     * client default) asks the server which tenant the credentials resolve to ({@code GET /api/v1/auth/me/}); the server
     * applies its own rule, the caller's first active membership. Lets an application that only knows the server URL
     * and an API key call tenant-scoped operations.
     */
    static String tenantOrLookup(HttpTransport http, String explicit) {
        String tenant = explicit != null ? explicit : http.options().tenantId();
        if (tenant == null) {
            tenant = http.config().tenantId();
        }
        if (tenant != null && !tenant.isBlank()) {
            return NovaConfig.normalizeTenantId(tenant);
        }
        UserMe me = http.send(ApiRequest.of(HttpMethod.GET, "auth/me/"), UserMe.class);
        CurrentTenant current = me == null ? null : me.currentTenant();
        if (current == null || current.id() == null || current.id().isBlank()) {
            throw new NovaClientValidationException(
                    "The server did not report a current tenant for these credentials; pass a tenant id explicitly.");
        }
        return NovaConfig.normalizeTenantId(current.id());
    }
}
