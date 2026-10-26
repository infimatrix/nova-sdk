package com.infimatrix.nova.resources;

import com.infimatrix.nova.Page;
import com.infimatrix.nova.Query;
import com.infimatrix.nova.http.ApiRequest;
import com.infimatrix.nova.http.HttpMethod;
import com.infimatrix.nova.http.HttpTransport;
import com.infimatrix.nova.models.BulkSendEmailRequest;
import com.infimatrix.nova.models.EmailBatchQueued;
import com.infimatrix.nova.models.EmailLog;
import com.infimatrix.nova.models.EmailPreview;
import com.infimatrix.nova.models.GroupSendEmailRequest;
import com.infimatrix.nova.models.SendEmailRequest;

/** Email dispatch and delivery logs. Dispatch calls are never retried automatically. */
public final class EmailsApi {
    private final HttpTransport http;

    /** Creates the API; obtained from the client. */
    public EmailsApi(HttpTransport http) {
        this.http = http;
    }

    /** {@code POST /api/v1/emails/logs/send/}: dispatches one transactional email. */
    public EmailLog send(SendEmailRequest request) {
        Validate.nonBlank(request.recipientEmail(), "recipient_email");
        Validate.nonBlank(request.subject(), "subject");
        return http.send(ApiRequest.of(HttpMethod.POST, "emails/logs/send/").json(request), EmailLog.class);
    }

    /** {@code POST /api/v1/emails/logs/bulk-send/}: sends a template to many contacts. */
    public EmailBatchQueued bulkSend(BulkSendEmailRequest request) {
        return http.send(ApiRequest.of(HttpMethod.POST, "emails/logs/bulk-send/").json(request), EmailBatchQueued.class);
    }

    /** {@code POST /api/v1/emails/logs/group-send/}: sends a template to every contact of a group. */
    public EmailBatchQueued groupSend(GroupSendEmailRequest request) {
        return http.send(ApiRequest.of(HttpMethod.POST, "emails/logs/group-send/").json(request), EmailBatchQueued.class);
    }

    /** {@code GET /api/v1/emails/logs/}; add {@code status} with {@code Query.builder().param("status", ...)}. */
    public Page<EmailLog> listLogs(Query query) {
        return http.listPage("emails/logs/", query, EmailLog.class);
    }

    /** {@code GET /api/v1/emails/logs/{id}/}. */
    public EmailPreview getLog(String logId) {
        return http.send(ApiRequest.of(HttpMethod.GET, "emails/logs/{}/", Validate.nonBlank(logId, "logId")),
                EmailPreview.class);
    }

    /** {@code GET /api/v1/emails/logs/{id}/preview/}. */
    public EmailPreview preview(String logId) {
        return http.send(ApiRequest.of(HttpMethod.GET, "emails/logs/{}/preview/", Validate.nonBlank(logId, "logId")),
                EmailPreview.class);
    }

    /** {@code GET /api/v1/emails/logs/export/}: delivery logs as CSV text. Filters: status, search, ordering. */
    public String exportCsv(Query query) {
        return http.sendText(ApiRequest.of(HttpMethod.GET, "emails/logs/export/").query(query));
    }

    /** Same as {@link #exportCsv(Query)} but returns the raw bytes. */
    public byte[] exportCsvBytes(Query query) {
        return http.sendBytes(ApiRequest.of(HttpMethod.GET, "emails/logs/export/").query(query));
    }
}
