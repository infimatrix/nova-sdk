import type { RequestOptions } from "../http.js";
import type { DashboardAnalytics } from "../schemas.js";
import { BaseResource } from "./base.js";

function isoDate(value: string | Date | undefined): string | undefined {
  if (value === undefined) return undefined;
  return value instanceof Date ? value.toISOString() : String(value).trim();
}

/** Dashboard metrics. */
export class AnalyticsResource extends BaseResource {
  /** `GET /api/v1/analytics/dashboard/`. Dates are `YYYY-MM-DD`/ISO strings or `Date`s. */
  async dashboard(
    query: { date_from?: string | Date; date_to?: string | Date } = {},
    options: RequestOptions = {},
  ): Promise<DashboardAnalytics> {
    const res = await this.http.request<DashboardAnalytics>("GET", "analytics/dashboard/", {
      ...options,
      params: { date_from: isoDate(query.date_from), date_to: isoDate(query.date_to) },
    });
    return res.data;
  }
}
