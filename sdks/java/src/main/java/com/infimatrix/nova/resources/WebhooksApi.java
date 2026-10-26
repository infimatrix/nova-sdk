package com.infimatrix.nova.resources;

import com.infimatrix.nova.Page;
import com.infimatrix.nova.Query;
import com.infimatrix.nova.http.ApiRequest;
import com.infimatrix.nova.http.HttpMethod;
import com.infimatrix.nova.http.HttpTransport;
import com.infimatrix.nova.models.PatchedWebhookEndpointCreateUpdateRequest;
import com.infimatrix.nova.models.TestWebhookRequest;
import com.infimatrix.nova.models.WebhookEndpoint;
import com.infimatrix.nova.models.WebhookEndpointCreateUpdate;
import com.infimatrix.nova.models.WebhookEndpointCreateUpdateRequest;
import com.infimatrix.nova.models.WebhookEventChoice;
import com.infimatrix.nova.models.WebhookSecretRotation;
import com.infimatrix.nova.models.WebhookTestDispatch;
import java.util.List;

/** Webhook endpoint subscriptions. */
public final class WebhooksApi {
    private final HttpTransport http;

    /** Creates the API; obtained from the client. */
    public WebhooksApi(HttpTransport http) {
        this.http = http;
    }

    /** {@code GET /api/v1/webhooks/}. */
    public Page<WebhookEndpoint> list(Query query) {
        return http.listPage("webhooks/", query, WebhookEndpoint.class);
    }

    /** {@code GET /api/v1/webhooks/{id}/}. */
    public WebhookEndpoint get(String webhookId) {
        return http.send(ApiRequest.of(HttpMethod.GET, "webhooks/{}/", Validate.nonBlank(webhookId, "webhookId")),
                WebhookEndpoint.class);
    }

    /** {@code POST /api/v1/webhooks/}. */
    public WebhookEndpointCreateUpdate create(WebhookEndpointCreateUpdateRequest request) {
        return http.send(ApiRequest.of(HttpMethod.POST, "webhooks/").json(request), WebhookEndpointCreateUpdate.class);
    }

    /** {@code PATCH /api/v1/webhooks/{id}/}. */
    public WebhookEndpointCreateUpdate update(String webhookId, PatchedWebhookEndpointCreateUpdateRequest request) {
        return http.send(ApiRequest.of(HttpMethod.PATCH, "webhooks/{}/", Validate.nonBlank(webhookId, "webhookId"))
                .json(request), WebhookEndpointCreateUpdate.class);
    }

    /** {@code DELETE /api/v1/webhooks/{id}/}. */
    public void delete(String webhookId) {
        http.send(ApiRequest.of(HttpMethod.DELETE, "webhooks/{}/", Validate.nonBlank(webhookId, "webhookId")));
    }

    /** {@code GET /api/v1/webhooks/events/}: events a webhook can subscribe to. */
    public List<WebhookEventChoice> events() {
        return http.sendList(ApiRequest.of(HttpMethod.GET, "webhooks/events/"), WebhookEventChoice.class);
    }

    /** {@code POST /api/v1/webhooks/{id}/rotate-secret/}: the new secret is returned <b>once</b>. */
    public WebhookSecretRotation rotateSecret(String webhookId) {
        return http.send(ApiRequest.of(HttpMethod.POST, "webhooks/{}/rotate-secret/", Validate.nonBlank(webhookId, "webhookId")),
                WebhookSecretRotation.class);
    }

    /** {@code POST /api/v1/webhooks/{id}/send-test/}: dispatches a <b>real</b> test event; {@code eventType} may be null. */
    public WebhookTestDispatch test(String webhookId, String eventType) {
        return http.send(ApiRequest.of(HttpMethod.POST, "webhooks/{}/send-test/", Validate.nonBlank(webhookId, "webhookId"))
                .json(TestWebhookRequest.builder().eventType(eventType).build()), WebhookTestDispatch.class);
    }
}
