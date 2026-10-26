import type { RequestOptions } from "../http.js";
import type { Page } from "../models.js";
import type {
  PatchedWebhookEndpointCreateUpdateRequest,
  TestWebhookRequest,
  WebhookEndpoint,
  WebhookEndpointCreateUpdate,
  WebhookEndpointCreateUpdateRequest,
  WebhookEventChoice,
  WebhookSecretRotation,
  WebhookTestDispatch,
} from "../schemas.js";
import { BaseResource, pathId, type ListQuery } from "./base.js";

/** Webhook endpoint subscriptions. */
export class WebhooksResource extends BaseResource {
  /** `GET /api/v1/webhooks/` */
  list(query: ListQuery = {}, options: RequestOptions = {}): Promise<Page<WebhookEndpoint>> {
    return this.listPage<WebhookEndpoint>("webhooks/", { ...query }, options);
  }

  /** `GET /api/v1/webhooks/{id}/` */
  async get(webhookId: string, options: RequestOptions = {}): Promise<WebhookEndpoint> {
    const res = await this.http.request<WebhookEndpoint>("GET", `webhooks/${pathId(webhookId, "webhookId")}/`, options);
    return res.data;
  }

  /** `POST /api/v1/webhooks/` */
  async create(body: WebhookEndpointCreateUpdateRequest, options: RequestOptions = {}): Promise<WebhookEndpointCreateUpdate> {
    const res = await this.http.request<WebhookEndpointCreateUpdate>("POST", "webhooks/", { ...options, json: body });
    return res.data;
  }

  /** `PATCH /api/v1/webhooks/{id}/` */
  async update(
    webhookId: string,
    body: PatchedWebhookEndpointCreateUpdateRequest,
    options: RequestOptions = {},
  ): Promise<WebhookEndpointCreateUpdate> {
    const res = await this.http.request<WebhookEndpointCreateUpdate>("PATCH", `webhooks/${pathId(webhookId, "webhookId")}/`, {
      ...options,
      json: body,
    });
    return res.data;
  }

  /** `DELETE /api/v1/webhooks/{id}/` */
  async delete(webhookId: string, options: RequestOptions = {}): Promise<void> {
    await this.http.request("DELETE", `webhooks/${pathId(webhookId, "webhookId")}/`, options);
  }

  /** `GET /api/v1/webhooks/events/`: events a webhook can subscribe to. */
  async events(options: RequestOptions = {}): Promise<WebhookEventChoice[]> {
    const res = await this.http.request<WebhookEventChoice[]>("GET", "webhooks/events/", options);
    return Array.isArray(res.data) ? res.data : [];
  }

  /** `POST /api/v1/webhooks/{id}/rotate-secret/`: the new secret is returned **once**. */
  async rotateSecret(webhookId: string, options: RequestOptions = {}): Promise<WebhookSecretRotation> {
    const res = await this.http.request<WebhookSecretRotation>(
      "POST",
      `webhooks/${pathId(webhookId, "webhookId")}/rotate-secret/`,
      options,
    );
    return res.data;
  }

  /** `POST /api/v1/webhooks/{id}/send-test/`: dispatch a real test event to the endpoint URL. */
  async test(webhookId: string, body: TestWebhookRequest = {}, options: RequestOptions = {}): Promise<WebhookTestDispatch> {
    const res = await this.http.request<WebhookTestDispatch>("POST", `webhooks/${pathId(webhookId, "webhookId")}/send-test/`, {
      ...options,
      json: body,
    });
    return res.data;
  }
}
