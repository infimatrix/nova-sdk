import {
  buildHeaders,
  normalizeTenantId,
  type NovaConfig,
} from "./config.js";
import {
  NovaAPIError,
  NovaAbortError,
  NovaConnectionError,
  NovaError,
  NovaRedirectError,
  NovaTimeoutError,
  NovaValidationError,
  mapApiError,
} from "./errors.js";
import type { ApiResponse, EnvelopeMeta } from "./models.js";

export type QueryValue = string | number | boolean | null | undefined | readonly (string | number | boolean)[];
export type QueryParams = Record<string, QueryValue>;

/** Options accepted by every SDK call as its last argument. */
export interface RequestOptions {
  /** Override the client's default tenant for this call (UUID). */
  tenantId?: string;
  /** Extra headers for this call. */
  headers?: Record<string, string>;
  /** Correlation ID sent as `X-Correlation-ID`. */
  correlationId?: string;
  /** Abort the call (and any pending retry wait). */
  signal?: AbortSignal;
  /** Override the per-attempt timeout (ms). */
  timeoutMs?: number;
}

/** Low-level request description used by {@link HttpTransport}. */
export interface TransportRequest extends RequestOptions {
  params?: QueryParams;
  /** JSON request body. */
  json?: unknown;
  /** Multipart / form body. */
  body?: FormData | URLSearchParams;
  /** Force (`true`) or forbid (`false`) automatic retries. Default: only GET/HEAD/OPTIONS retry. */
  allowRetry?: boolean;
}

const IDEMPOTENT_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);
const MAX_RETRY_AFTER_SECONDS = 30;

type Logger = { warn(message: string): void };

function noopLogger(): Logger {
  return { warn() {} };
}

/** HTTP engine: auth, tenancy, timeouts, bounded retries, envelope parsing, typed errors. */
export class HttpTransport {
  constructor(
    readonly config: NovaConfig,
    private readonly logger: Logger = noopLogger(),
  ) {}

  /** Build the absolute URL for an endpoint below `/api/v1/`. */
  buildUrl(endpoint: string, params?: QueryParams): string {
    const [pathPart = "", ...queryParts] = endpoint.trim().split("?");
    let path = pathPart.replace(/^\/+/, "");
    if (path === "api/v1") path = "";
    else if (path.startsWith("api/v1/")) path = path.slice("api/v1/".length).replace(/^\/+/, "");

    // An id of "." or ".." would be normalised away by fetch/intermediaries and address another endpoint.
    for (const segment of path.split("/")) {
      let decoded = segment;
      try {
        decoded = decodeURIComponent(segment);
      } catch {
        // malformed escape: leave as is, it cannot be a dot-segment
      }
      if (decoded === "." || decoded === "..") {
        throw new NovaValidationError("Path identifiers must not be '.' or '..'.");
      }
    }

    if (path && !path.endsWith("/")) {
      const last = path.split("/").pop() ?? "";
      const dot = last.lastIndexOf(".");
      const ext = dot >= 0 ? last.slice(dot).toLowerCase() : "";
      if (!KNOWN_FILE_EXTENSIONS.has(ext)) path += "/";
    }

    const search = new URLSearchParams(queryParts.join("?"));
    for (const [key, value] of Object.entries(params ?? {})) {
      if (value === undefined || value === null) continue;
      if (Array.isArray(value)) for (const item of value) search.append(key, String(item));
      else search.append(key, String(value));
    }
    const qs = search.toString();
    return `${this.config.baseUrl}/api/v1/${path}${qs ? `?${qs}` : ""}`;
  }

  /** Perform a request and return the raw `fetch` response (2xx only; errors are thrown). */
  async requestRaw(method: string, endpoint: string, req: TransportRequest = {}): Promise<Response> {
    const httpMethod = method.trim().toUpperCase();
    const url = this.buildUrl(endpoint, req.params);
    const headers = this.prepareHeaders(req);

    let body: NonNullable<RequestInit["body"]> | undefined;
    if (req.json !== undefined) {
      body = JSON.stringify(req.json);
      headers["Content-Type"] = "application/json";
    } else if (req.body !== undefined) {
      body = req.body; // fetch sets the multipart boundary / urlencoded type itself
    }

    const safeToRetry = req.allowRetry ?? IDEMPOTENT_METHODS.has(httpMethod);
    const maxAttempts = safeToRetry ? this.config.maxRetries + 1 : 1;
    const correlationId = headers["X-Correlation-ID"];
    const timeoutMs = req.timeoutMs ?? this.config.timeoutMs;

    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const last = attempt >= maxAttempts - 1;
      const { signal, cleanup, timedOut } = this.attemptSignal(req.signal, timeoutMs);
      let response: Response;
      try {
        response = await this.config.fetch(url, {
          method: httpMethod,
          headers,
          body,
          redirect: "manual", // never forward credentials across redirect hops
          signal,
        });
      } catch (error) {
        cleanup();
        if (req.signal?.aborted) throw new NovaAbortError("Request was aborted.", { correlationId, cause: error });
        const timeout = timedOut();
        if (!last) {
          await this.sleep(this.backoffDelay(attempt), req.signal);
          this.logger.warn(`Nova ${httpMethod} ${endpoint} ${timeout ? "timed out" : "failed"}; retrying`);
          continue;
        }
        if (timeout) {
          throw new NovaTimeoutError(`Request to Nova API timed out after ${timeoutMs}ms.`, { correlationId, cause: error });
        }
        throw new NovaConnectionError(`Failed to connect to Nova API at ${this.config.baseUrl}: ${describe(error)}`, {
          correlationId,
          cause: error,
        });
      }
      cleanup();

      if (response.status >= 200 && response.status < 300) return response;

      if (response.status >= 300 && response.status < 400) {
        throw this.redirectError(response);
      }

      if (!last && this.config.retryableStatusCodes.includes(response.status)) {
        const delay = this.backoffDelay(attempt, parseRetryAfter(response));
        await response.body?.cancel().catch(() => undefined);
        this.logger.warn(`Nova ${httpMethod} ${endpoint} returned ${response.status}; retrying in ${delay}ms`);
        await this.sleep(delay, req.signal);
        continue;
      }
      throw await this.errorFromResponse(response);
    }
    throw new NovaError("Request terminated without a response.", { correlationId });
  }

  /** Perform a request and unwrap the Nova response envelope. */
  async request<T = unknown>(method: string, endpoint: string, req: TransportRequest = {}): Promise<ApiResponse<T>> {
    const response = await this.requestRaw(method, endpoint, req);
    return this.parseSuccess<T>(response);
  }

  // -- internals --------------------------------------------------------------

  private prepareHeaders(req: TransportRequest): Record<string, string> {
    const headers = buildHeaders(this.config);
    if (req.tenantId) headers["X-Tenant-ID"] = normalizeTenantId(req.tenantId);
    if (req.correlationId) headers["X-Correlation-ID"] = req.correlationId.trim();
    if (req.headers) Object.assign(headers, req.headers);
    return headers;
  }

  /** Combine the caller's signal with a per-attempt timeout. */
  private attemptSignal(external: AbortSignal | undefined, timeoutMs: number) {
    const controller = new AbortController();
    let didTimeOut = false;
    const timer = setTimeout(() => {
      didTimeOut = true;
      controller.abort(new Error("timeout"));
    }, timeoutMs);
    const onAbort = () => controller.abort(external?.reason);
    if (external) {
      if (external.aborted) onAbort();
      else external.addEventListener("abort", onAbort, { once: true });
    }
    return {
      signal: controller.signal,
      timedOut: () => didTimeOut,
      cleanup: () => {
        clearTimeout(timer);
        external?.removeEventListener("abort", onAbort);
      },
    };
  }

  private backoffDelay(attempt: number, retryAfterSeconds?: number): number {
    if (retryAfterSeconds !== undefined) {
      return Math.min(MAX_RETRY_AFTER_SECONDS, retryAfterSeconds) * 1000;
    }
    let delay = this.config.retryBackoffMs * 2 ** attempt;
    if (this.config.retryJitter) delay *= 0.5 + Math.random() * 0.5;
    return Math.min(MAX_RETRY_AFTER_SECONDS * 1000, Math.max(50, delay));
  }

  private sleep(ms: number, signal?: AbortSignal): Promise<void> {
    return new Promise((resolve, reject) => {
      if (signal?.aborted) return reject(new NovaAbortError("Request was aborted."));
      const timer = setTimeout(() => {
        signal?.removeEventListener("abort", onAbort);
        resolve();
      }, ms);
      const onAbort = () => {
        clearTimeout(timer);
        reject(new NovaAbortError("Request was aborted."));
      };
      signal?.addEventListener("abort", onAbort, { once: true });
    });
  }

  private redirectError(response: Response): NovaRedirectError {
    const location = sanitizeRedirectLocation(response.headers.get("Location"));
    return new NovaRedirectError(`Unexpected HTTP ${response.status} redirect${location ? ` to ${location}` : ""}.`, {
      statusCode: response.status,
      details: location ? { location } : {},
      correlationId: response.headers.get("X-Correlation-ID") ?? undefined,
      location,
    });
  }

  private async parseSuccess<T>(response: Response): Promise<ApiResponse<T>> {
    const correlationId = response.headers.get("X-Correlation-ID") ?? undefined;
    const meta: EnvelopeMeta = correlationId ? { correlation_id: correlationId } : {};

    if (response.status === 204) {
      return { data: null as T, success: true, message: "Operation completed successfully.", meta };
    }
    const text = await response.text();
    if (!text) return { data: null as T, success: true, message: "Operation completed successfully.", meta };

    const contentType = response.headers.get("Content-Type") ?? "";
    if (contentType.includes("text/csv")) {
      return { data: text as T, success: true, message: "CSV export generated.", meta };
    }

    let payload: unknown;
    try {
      payload = JSON.parse(text);
    } catch {
      if (contentType.toLowerCase().includes("json")) {
        // The server declared JSON but sent something else: never report that as success.
        throw new NovaAPIError(`Invalid JSON in HTTP ${response.status} response.`, {
          statusCode: response.status,
          errorCode: "INVALID_RESPONSE",
          correlationId,
        });
      }
      return { data: text as T, success: true, message: "Raw response received.", meta };
    }

    if (isRecord(payload) && "success" in payload && "data" in payload) {
      const envelopeMeta: EnvelopeMeta = isRecord(payload["meta"]) ? { ...(payload["meta"] as EnvelopeMeta) } : {};
      if (!envelopeMeta.correlation_id && correlationId) envelopeMeta.correlation_id = correlationId;
      return {
        data: payload["data"] as T,
        success: Boolean(payload["success"]),
        message: typeof payload["message"] === "string" ? payload["message"] : "Operation completed successfully.",
        meta: envelopeMeta,
      };
    }
    return { data: payload as T, success: true, message: "Operation completed successfully.", meta };
  }

  private async errorFromResponse(response: Response): Promise<NovaError> {
    let correlationId = response.headers.get("X-Correlation-ID") ?? undefined;
    const retryAfter = parseRetryAfter(response);
    const text = await response.text().catch(() => "");

    let message: string | undefined;
    let errorCode: string | undefined;
    let details: unknown;

    try {
      const payload: unknown = JSON.parse(text);
      if (isRecord(payload)) {
        const meta = payload["meta"];
        if (isRecord(meta) && typeof meta["correlation_id"] === "string") correlationId = meta["correlation_id"];

        const errObj = payload["error"] || payload["errors"];
        if (isRecord(errObj)) {
          if (typeof errObj["code"] === "string") errorCode = errObj["code"];
          if (typeof errObj["message"] === "string") message = errObj["message"];
          details = errObj["details"];
        } else if (typeof errObj === "string") {
          message = errObj; // legacy bodies such as {"error": "Tenant context required."}
        }
        if (!message) {
          const top = payload["message"] || payload["detail"];
          if (typeof top === "string") message = top;
        }
        if (details === undefined || details === null) {
          const SKIP = new Set(["success", "message", "error", "errors", "meta", "data"]);
          details = Object.fromEntries(Object.entries(payload).filter(([key]) => !SKIP.has(key)));
        }
      } else if (Array.isArray(payload)) {
        details = { errors: payload };
        message = "Validation failed for request data.";
      }
    } catch {
      message = sanitizeErrorText(text, response.status);
    }
    if (!message) message = sanitizeErrorText(text, response.status);

    return mapApiError(response.status, { message, errorCode, details, correlationId, retryAfter });
  }
}

const KNOWN_FILE_EXTENSIONS = new Set([
  ".csv", ".gif", ".gz", ".htm", ".html", ".jpeg", ".jpg", ".json", ".pdf", ".png",
  ".svg", ".tar", ".txt", ".webp", ".xml", ".yaml", ".yml", ".zip",
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function describe(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function parseRetryAfter(response: Response): number | undefined {
  const header = response.headers.get("Retry-After");
  if (!header) return undefined;
  const seconds = Number(header);
  return Number.isFinite(seconds) ? Math.max(0, seconds) : undefined;
}

/** Remove embedded credentials from a redirect target before it reaches an error message. */
export function sanitizeRedirectLocation(location: string | null): string | undefined {
  if (!location?.trim()) return undefined;
  try {
    const url = new URL(location.trim());
    url.username = "";
    url.password = "";
    return url.toString();
  } catch {
    return location.trim().includes("@") ? "<invalid-redirect-url>" : location.trim();
  }
}

/** Reduce a non-JSON or HTML error body to a short, safe summary. */
export function sanitizeErrorText(text: string | undefined, status: number): string {
  const raw = (text ?? "").trim();
  if (!raw) return `HTTP ${status} Error`;
  const lower = raw.toLowerCase();
  if (lower.includes("<html") || lower.includes("<!doctype html") || lower.includes("<head") || lower.includes("<body")) {
    const title = /<title>([\s\S]*?)<\/title>/i.exec(raw)?.[1]?.replace(/\s+/g, " ").trim();
    return title && title.length <= 120 ? `HTTP ${status} Error: ${title}` : `HTTP ${status} Error (HTML response received)`;
  }
  const collapsed = raw.replace(/\s+/g, " ");
  return collapsed.length > 200 ? `${collapsed.slice(0, 197)}...` : collapsed;
}
