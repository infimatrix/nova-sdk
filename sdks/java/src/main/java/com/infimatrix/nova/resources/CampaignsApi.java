package com.infimatrix.nova.resources;

import com.infimatrix.nova.Page;
import com.infimatrix.nova.Query;
import com.infimatrix.nova.http.ApiRequest;
import com.infimatrix.nova.http.HttpMethod;
import com.infimatrix.nova.http.HttpTransport;
import com.infimatrix.nova.models.PatchedTransactionalNotificationRequest;
import com.infimatrix.nova.models.SendTestEmailRequest;
import com.infimatrix.nova.models.TransactionalNotification;
import com.infimatrix.nova.models.TransactionalNotificationRequest;
import com.infimatrix.nova.models.TransactionalTestDispatch;

/** Transactional notification definitions. */
public final class CampaignsApi {
    private final HttpTransport http;

    /** Creates the API; obtained from the client. */
    public CampaignsApi(HttpTransport http) {
        this.http = http;
    }

    /** {@code GET /api/v1/campaigns/transactional/}. */
    public Page<TransactionalNotification> list(Query query) {
        return http.listPage("campaigns/transactional/", query, TransactionalNotification.class);
    }

    /** {@code GET /api/v1/campaigns/transactional/{id}/}. */
    public TransactionalNotification get(String notificationId) {
        return http.send(ApiRequest.of(HttpMethod.GET, "campaigns/transactional/{}/",
                Validate.nonBlank(notificationId, "notificationId")), TransactionalNotification.class);
    }

    /** {@code POST /api/v1/campaigns/transactional/}. */
    public TransactionalNotification create(TransactionalNotificationRequest request) {
        return http.send(ApiRequest.of(HttpMethod.POST, "campaigns/transactional/").json(request),
                TransactionalNotification.class);
    }

    /** {@code PATCH /api/v1/campaigns/transactional/{id}/}. */
    public TransactionalNotification update(String notificationId, PatchedTransactionalNotificationRequest request) {
        return http.send(ApiRequest.of(HttpMethod.PATCH, "campaigns/transactional/{}/",
                Validate.nonBlank(notificationId, "notificationId")).json(request), TransactionalNotification.class);
    }

    /** {@code DELETE /api/v1/campaigns/transactional/{id}/}. */
    public void delete(String notificationId) {
        http.send(ApiRequest.of(HttpMethod.DELETE, "campaigns/transactional/{}/",
                Validate.nonBlank(notificationId, "notificationId")));
    }

    /** {@code POST /api/v1/campaigns/transactional/{id}/send-test/}: queues a <b>real</b> test email. */
    public TransactionalTestDispatch sendTest(String notificationId, SendTestEmailRequest request) {
        Validate.nonBlank(request.recipientEmail(), "recipient_email");
        return http.send(ApiRequest.of(HttpMethod.POST, "campaigns/transactional/{}/send-test/",
                Validate.nonBlank(notificationId, "notificationId")).json(request), TransactionalTestDispatch.class);
    }
}
