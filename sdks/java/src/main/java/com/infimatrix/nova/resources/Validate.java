package com.infimatrix.nova.resources;

import com.infimatrix.nova.NovaConfig;
import com.infimatrix.nova.errors.NovaClientValidationException;
import com.infimatrix.nova.http.HttpTransport;

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
}
