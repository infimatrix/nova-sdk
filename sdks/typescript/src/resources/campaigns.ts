import type { HttpTransport, RequestOptions } from "../http.js";
import type { Page } from "../models.js";
import type {
  PatchedTransactionalNotificationRequest,
  SendTestEmailRequest,
  TransactionalNotification,
  TransactionalNotificationRequest,
  TransactionalTestDispatch,
} from "../schemas.js";
import { BaseResource, pathId, requireString, type ListQuery } from "./base.js";

/** Transactional notification definitions. */
export class TransactionalNotificationsResource extends BaseResource {
  /** `GET /api/v1/campaigns/transactional/` */
  list(query: ListQuery = {}, options: RequestOptions = {}): Promise<Page<TransactionalNotification>> {
    return this.listPage<TransactionalNotification>("campaigns/transactional/", { ...query }, options);
  }

  /** `GET /api/v1/campaigns/transactional/{id}/` */
  async get(notificationId: string, options: RequestOptions = {}): Promise<TransactionalNotification> {
    const res = await this.http.request<TransactionalNotification>(
      "GET",
      `campaigns/transactional/${pathId(notificationId, "notificationId")}/`,
      options,
    );
    return res.data;
  }

  /** `POST /api/v1/campaigns/transactional/` */
  async create(body: TransactionalNotificationRequest, options: RequestOptions = {}): Promise<TransactionalNotification> {
    const res = await this.http.request<TransactionalNotification>("POST", "campaigns/transactional/", {
      ...options,
      json: body,
    });
    return res.data;
  }

  /** `PATCH /api/v1/campaigns/transactional/{id}/` */
  async update(
    notificationId: string,
    body: PatchedTransactionalNotificationRequest,
    options: RequestOptions = {},
  ): Promise<TransactionalNotification> {
    const res = await this.http.request<TransactionalNotification>(
      "PATCH",
      `campaigns/transactional/${pathId(notificationId, "notificationId")}/`,
      { ...options, json: body },
    );
    return res.data;
  }

  /** `DELETE /api/v1/campaigns/transactional/{id}/` */
  async delete(notificationId: string, options: RequestOptions = {}): Promise<void> {
    await this.http.request("DELETE", `campaigns/transactional/${pathId(notificationId, "notificationId")}/`, options);
  }

  /** `POST /api/v1/campaigns/transactional/{id}/send-test/`: queues a **real** test email. */
  async sendTest(
    notificationId: string,
    body: SendTestEmailRequest,
    options: RequestOptions = {},
  ): Promise<TransactionalTestDispatch> {
    const payload = { ...body, recipient_email: requireString(body.recipient_email, "recipient_email") };
    const res = await this.http.request<TransactionalTestDispatch>(
      "POST",
      `campaigns/transactional/${pathId(notificationId, "notificationId")}/send-test/`,
      { ...options, json: payload },
    );
    return res.data;
  }
}

/** Campaign operations. Currently exposes transactional notifications. */
export class CampaignsResource extends BaseResource {
  readonly transactional: TransactionalNotificationsResource;

  constructor(http: HttpTransport) {
    super(http);
    this.transactional = new TransactionalNotificationsResource(http);
  }

  list(query: ListQuery = {}, options: RequestOptions = {}) {
    return this.transactional.list(query, options);
  }
  get(notificationId: string, options: RequestOptions = {}) {
    return this.transactional.get(notificationId, options);
  }
  create(body: TransactionalNotificationRequest, options: RequestOptions = {}) {
    return this.transactional.create(body, options);
  }
  update(notificationId: string, body: PatchedTransactionalNotificationRequest, options: RequestOptions = {}) {
    return this.transactional.update(notificationId, body, options);
  }
  delete(notificationId: string, options: RequestOptions = {}) {
    return this.transactional.delete(notificationId, options);
  }
  sendTest(notificationId: string, body: SendTestEmailRequest, options: RequestOptions = {}) {
    return this.transactional.sendTest(notificationId, body, options);
  }
}
