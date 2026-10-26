import { NovaValidationError } from "../errors.js";
import type { HttpTransport, QueryParams, RequestOptions } from "../http.js";
import { Page } from "../models.js";

/** Common query parameters of list endpoints. */
export interface ListQuery {
  search?: string;
  ordering?: string;
  /** 1-based page number. */
  page?: number;
  page_size?: number;
}

/** Validate and URL-encode a path identifier. */
export function pathId(value: unknown, label: string): string {
  if (typeof value !== "string" && typeof value !== "number") {
    throw new NovaValidationError(`${label} must be a non-empty string.`);
  }
  const clean = String(value).trim();
  if (!clean) throw new NovaValidationError(`${label} must be a non-empty string.`);
  return encodeURIComponent(clean);
}

/** Require a non-empty string field. */
export function requireString(value: unknown, label: string): string {
  if (typeof value !== "string" || !value.trim()) {
    throw new NovaValidationError(`${label} must be a non-empty string.`);
  }
  return value.trim();
}

/** Base class for resource clients. */
export abstract class BaseResource {
  constructor(protected readonly http: HttpTransport) {}

  /** GET a list endpoint and wrap it as an auto-paginating {@link Page}. */
  protected async listPage<T>(endpoint: string, query: QueryParams = {}, options: RequestOptions = {}): Promise<Page<T>> {
    const response = await this.http.request("GET", endpoint, { ...options, params: query });
    return Page.fromResponse<T>(response, (page) =>
      this.listPage<T>(endpoint, { ...query, page }, options),
    );
  }
}
