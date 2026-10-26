import type { RequestOptions } from "../http.js";
import type { Page } from "../models.js";
import type {
  BulkSendEmailRequest,
  EmailBatchQueued,
  EmailLog,
  EmailMessageStatusEnum,
  EmailPreview,
  GroupSendEmailRequest,
  SendEmailRequest,
} from "../schemas.js";
import { BaseResource, pathId, requireString, type ListQuery } from "./base.js";

export interface EmailLogQuery extends ListQuery {
  /** Filter by delivery status (case-insensitive); `ALL` disables filtering. */
  status?: EmailMessageStatusEnum | string;
}

/** Email dispatch and delivery logs. Dispatch calls are never retried automatically. */
export class EmailsResource extends BaseResource {
  /** `POST /api/v1/emails/logs/send/`: dispatch one transactional email. */
  async send(body: SendEmailRequest, options: RequestOptions = {}): Promise<EmailLog> {
    const payload = {
      ...body,
      recipient_email: requireString(body.recipient_email, "recipient_email"),
      subject: requireString(body.subject, "subject"),
    };
    const res = await this.http.request<EmailLog>("POST", "emails/logs/send/", { ...options, json: payload });
    return res.data;
  }

  /** `POST /api/v1/emails/logs/bulk-send/`: send a template to many contacts. */
  async bulkSend(body: BulkSendEmailRequest, options: RequestOptions = {}): Promise<EmailBatchQueued> {
    const res = await this.http.request<EmailBatchQueued>("POST", "emails/logs/bulk-send/", { ...options, json: body });
    return res.data;
  }

  /** `POST /api/v1/emails/logs/group-send/`: send a template to every contact of a group. */
  async groupSend(body: GroupSendEmailRequest, options: RequestOptions = {}): Promise<EmailBatchQueued> {
    const res = await this.http.request<EmailBatchQueued>("POST", "emails/logs/group-send/", { ...options, json: body });
    return res.data;
  }

  /** `GET /api/v1/emails/logs/` */
  listLogs(query: EmailLogQuery = {}, options: RequestOptions = {}): Promise<Page<EmailLog>> {
    return this.listPage<EmailLog>("emails/logs/", { ...query }, options);
  }

  /** `GET /api/v1/emails/logs/{id}/` */
  async getLog(logId: string, options: RequestOptions = {}): Promise<EmailPreview> {
    const res = await this.http.request<EmailPreview>("GET", `emails/logs/${pathId(logId, "logId")}/`, options);
    return res.data;
  }

  /** `GET /api/v1/emails/logs/{id}/preview/` */
  async preview(logId: string, options: RequestOptions = {}): Promise<EmailPreview> {
    const res = await this.http.request<EmailPreview>("GET", `emails/logs/${pathId(logId, "logId")}/preview/`, options);
    return res.data;
  }

  /** `GET /api/v1/emails/logs/export/`: delivery logs as CSV text. */
  async exportCsv(query: Pick<EmailLogQuery, "status" | "search" | "ordering"> = {}, options: RequestOptions = {}): Promise<string> {
    const res = await this.http.request<string>("GET", "emails/logs/export/", { ...options, params: { ...query } });
    return String(res.data ?? "");
  }

  /** Same as {@link exportCsv} but returns the raw bytes. */
  async exportCsvBytes(
    query: Pick<EmailLogQuery, "status" | "search" | "ordering"> = {},
    options: RequestOptions = {},
  ): Promise<Uint8Array> {
    const response = await this.http.requestRaw("GET", "emails/logs/export/", { ...options, params: { ...query } });
    return new Uint8Array(await response.arrayBuffer());
  }
}
