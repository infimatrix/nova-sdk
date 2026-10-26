package com.infimatrix.nova.resources;

import com.infimatrix.nova.Page;
import com.infimatrix.nova.Query;
import com.infimatrix.nova.http.ApiRequest;
import com.infimatrix.nova.http.HttpMethod;
import com.infimatrix.nova.http.HttpTransport;
import com.infimatrix.nova.models.AccessLog;
import com.infimatrix.nova.models.AccessLogStats;
import com.infimatrix.nova.models.AccessLogSummary;

/** Tenant access audit logs. */
public final class AuditApi {
    private final HttpTransport http;

    /** Creates the API; obtained from the client. */
    public AuditApi(HttpTransport http) {
        this.http = http;
    }

    /**
     * {@code GET /api/v1/audit/access-logs/}. Filters are passed through {@link Query#builder()} (for example
     * {@code category}, {@code status_code_gte}, {@code created_after}).
     */
    public Page<AccessLogSummary> list(Query query) {
        return http.listPage("audit/access-logs/", query, AccessLogSummary.class);
    }

    /** {@code GET /api/v1/audit/access-logs/{id}/}. */
    public AccessLog get(String logId) {
        return http.send(ApiRequest.of(HttpMethod.GET, "audit/access-logs/{}/", Validate.nonBlank(logId, "logId")),
                AccessLog.class);
    }

    /** {@code GET /api/v1/audit/access-logs/stats/}: aggregate statistics (tenant admins only). */
    public AccessLogStats stats() {
        return http.send(ApiRequest.of(HttpMethod.GET, "audit/access-logs/stats/"), AccessLogStats.class);
    }
}
