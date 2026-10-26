package com.infimatrix.nova.resources;

import com.infimatrix.nova.Query;
import com.infimatrix.nova.http.ApiRequest;
import com.infimatrix.nova.http.HttpMethod;
import com.infimatrix.nova.http.HttpTransport;
import com.infimatrix.nova.models.DashboardAnalytics;

/** Dashboard metrics. */
public final class AnalyticsApi {
    private final HttpTransport http;

    /** Creates the API; obtained from the client. */
    public AnalyticsApi(HttpTransport http) {
        this.http = http;
    }

    /** {@code GET /api/v1/analytics/dashboard/}; dates are {@code YYYY-MM-DD} or ISO-8601 strings (may be null). */
    public DashboardAnalytics dashboard(String dateFrom, String dateTo) {
        return http.send(ApiRequest.of(HttpMethod.GET, "analytics/dashboard/")
                .query(Query.builder().param("date_from", dateFrom).param("date_to", dateTo).build()),
                DashboardAnalytics.class);
    }
}
