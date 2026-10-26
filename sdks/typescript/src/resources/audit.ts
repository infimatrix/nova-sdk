import type { HttpTransport, RequestOptions } from "../http.js";
import type { Page } from "../models.js";
import type { AccessLog, AccessLogStats, AccessLogSummary, CategoryEnum } from "../schemas.js";
import { BaseResource, pathId, type ListQuery } from "./base.js";

export interface AccessLogQuery extends ListQuery {
  category?: CategoryEnum | string;
  /** User UUID. */
  user?: string;
  user_email?: string;
  action?: string;
  http_method?: string;
  status_code?: number;
  status_code_gte?: number;
  status_code_lte?: number;
  resource_type?: string;
  resource_id?: string;
  ip_address?: string;
  created_after?: string | Date;
  created_before?: string | Date;
}

function normalize(query: AccessLogQuery) {
  const { created_after, created_before, ...rest } = query;
  return {
    ...rest,
    created_after: created_after instanceof Date ? created_after.toISOString() : created_after,
    created_before: created_before instanceof Date ? created_before.toISOString() : created_before,
  };
}

/** Tenant access audit logs. */
export class AccessLogsResource extends BaseResource {
  /** `GET /api/v1/audit/access-logs/` */
  list(query: AccessLogQuery = {}, options: RequestOptions = {}): Promise<Page<AccessLogSummary>> {
    return this.listPage<AccessLogSummary>("audit/access-logs/", normalize(query), options);
  }

  /** `GET /api/v1/audit/access-logs/{id}/` */
  async get(logId: string, options: RequestOptions = {}): Promise<AccessLog> {
    const res = await this.http.request<AccessLog>("GET", `audit/access-logs/${pathId(logId, "logId")}/`, options);
    return res.data;
  }

  /** `GET /api/v1/audit/access-logs/stats/`: aggregate statistics (tenant admins only). */
  async stats(options: RequestOptions = {}): Promise<AccessLogStats> {
    const res = await this.http.request<AccessLogStats>("GET", "audit/access-logs/stats/", options);
    return res.data;
  }
}

/** Audit and compliance logging. */
export class AuditResource extends BaseResource {
  readonly accessLogs: AccessLogsResource;

  constructor(http: HttpTransport) {
    super(http);
    this.accessLogs = new AccessLogsResource(http);
  }

  list(query: AccessLogQuery = {}, options: RequestOptions = {}) {
    return this.accessLogs.list(query, options);
  }
  get(logId: string, options: RequestOptions = {}) {
    return this.accessLogs.get(logId, options);
  }
  stats(options: RequestOptions = {}) {
    return this.accessLogs.stats(options);
  }
}
