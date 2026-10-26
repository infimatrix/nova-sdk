import { NovaValidationError } from "./errors.js";
import { VERSION } from "./version.js";

export type FetchLike = (input: string, init?: RequestInit) => Promise<Response>;

/** Options accepted by {@link NovaClient}. */
export interface NovaClientOptions {
  /** API origin, e.g. `https://api.example.com`. Env: `NOVA_BASE_URL`. Default `http://localhost:8000`. */
  baseUrl?: string;
  /** Nova API key (`nova_key_…`). Env: `NOVA_API_KEY`. Takes precedence over `accessToken`. */
  apiKey?: string;
  /** JWT access token. Env: `NOVA_ACCESS_TOKEN`. */
  accessToken?: string;
  /** Default tenant (workspace) UUID sent as `X-Tenant-ID`. Env: `NOVA_TENANT_ID`. */
  tenantId?: string;
  /** Per-attempt request timeout in milliseconds. Default 30 000. */
  timeoutMs?: number;
  /** Maximum retries for transient failures of idempotent requests (0–10). Default 3. */
  maxRetries?: number;
  /** Exponential backoff base in milliseconds. Default 500. */
  retryBackoffMs?: number;
  /** Randomise backoff delays. Default true. */
  retryJitter?: boolean;
  /** Headers added to every request. */
  defaultHeaders?: Record<string, string>;
  /** Custom `fetch` implementation (proxies, tests). Defaults to the global `fetch`. */
  fetch?: FetchLike;
  /**
   * Allow constructing a client with credentials in a browser. API keys and tokens
   * are secrets and must not ship in client-side code; this exists for trusted
   * environments only (for example an internal tool behind SSO).
   */
  dangerouslyAllowBrowser?: boolean;
}

/** Validated, normalised configuration. */
export interface NovaConfig {
  baseUrl: string;
  apiKey?: string;
  accessToken?: string;
  tenantId?: string;
  timeoutMs: number;
  maxRetries: number;
  retryBackoffMs: number;
  retryJitter: boolean;
  retryableStatusCodes: readonly number[];
  defaultHeaders: Record<string, string>;
  fetch: FetchLike;
}

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export const DEFAULT_RETRYABLE_STATUS_CODES = [429, 502, 503, 504] as const;

function env(name: string): string | undefined {
  const value = (globalThis as { process?: { env?: Record<string, string | undefined> } })
    .process?.env?.[name];
  return value === undefined || value === "" ? undefined : value;
}

/** Strip whitespace and any leading `Bearer ` prefix(es) from a credential. */
export function cleanCredential(value: string | null | undefined): string | undefined {
  if (value === null || value === undefined) return undefined;
  let cleaned = String(value).trim();
  for (;;) {
    const lower = cleaned.toLowerCase();
    if (lower === "bearer") return undefined;
    if (!lower.startsWith("bearer ")) break;
    cleaned = cleaned.slice(7).trim();
  }
  return cleaned || undefined;
}

/** Mask a credential for display. */
export function redact(value: string | null | undefined): string {
  const cleaned = cleanCredential(value);
  if (!cleaned) return "<none>";
  return cleaned.length <= 12 ? "[REDACTED]" : `${cleaned.slice(0, 8)}...[REDACTED]`;
}

/** Validate a tenant UUID and return it in canonical (lower-case) form. */
export function normalizeTenantId(value: string): string {
  const trimmed = String(value).trim();
  if (!UUID_RE.test(trimmed)) {
    throw new NovaValidationError(`tenant_id must be a valid UUID string, got ${JSON.stringify(value)}.`);
  }
  return trimmed.toLowerCase();
}

function isBrowser(): boolean {
  const g = globalThis as { window?: unknown; document?: unknown };
  return typeof g.window !== "undefined" && typeof g.document !== "undefined";
}

/** Resolve options + environment into a validated {@link NovaConfig}. */
export function resolveConfig(options: NovaClientOptions = {}): NovaConfig {
  const rawBase = options.baseUrl ?? env("NOVA_BASE_URL") ?? "http://localhost:8000";
  let url: URL;
  try {
    url = new URL(rawBase.trim());
  } catch {
    throw new NovaValidationError(`Invalid baseUrl ${JSON.stringify(rawBase)}. Must be an absolute http(s) URL.`);
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new NovaValidationError(`Invalid baseUrl scheme ${JSON.stringify(url.protocol)}. Must be 'http' or 'https'.`);
  }
  const baseUrl = (url.origin + url.pathname).replace(/\/+$/, "").replace(/\/api(\/v1)?$/, "");

  const timeoutMs = options.timeoutMs ?? 30_000;
  if (typeof timeoutMs !== "number" || !Number.isFinite(timeoutMs) || timeoutMs <= 0) {
    throw new NovaValidationError(`timeoutMs must be a positive number, got ${String(timeoutMs)}.`);
  }
  const maxRetries = options.maxRetries ?? 3;
  if (!Number.isInteger(maxRetries) || maxRetries < 0) {
    throw new NovaValidationError(`maxRetries must be a non-negative integer, got ${String(maxRetries)}.`);
  }
  if (maxRetries > 10) {
    throw new NovaValidationError(`maxRetries cannot exceed 10 for safety, got ${maxRetries}.`);
  }
  const retryBackoffMs = options.retryBackoffMs ?? 500;
  if (typeof retryBackoffMs !== "number" || !(retryBackoffMs >= 0)) {
    throw new NovaValidationError("retryBackoffMs must be a non-negative number.");
  }

  const tenantRaw = options.tenantId ?? env("NOVA_TENANT_ID");
  const apiKey = cleanCredential(options.apiKey ?? env("NOVA_API_KEY"));
  const accessToken = cleanCredential(options.accessToken ?? env("NOVA_ACCESS_TOKEN"));

  if (isBrowser() && !options.dangerouslyAllowBrowser && (apiKey || accessToken)) {
    throw new NovaValidationError(
      "Refusing to use Nova credentials in a browser: API keys and tokens would be exposed to end users. " +
        "Call Nova from your server instead, or set dangerouslyAllowBrowser: true if you accept the risk.",
    );
  }

  const fetchImpl: FetchLike | undefined =
    options.fetch ?? (typeof globalThis.fetch === "function" ? globalThis.fetch.bind(globalThis) : undefined);
  if (!fetchImpl) {
    throw new NovaValidationError("No fetch implementation found. Use Node.js 18+ or pass options.fetch.");
  }

  const config: NovaConfig = {
    baseUrl,
    tenantId: tenantRaw ? normalizeTenantId(tenantRaw) : undefined,
    timeoutMs,
    maxRetries,
    retryBackoffMs,
    retryJitter: options.retryJitter ?? true,
    retryableStatusCodes: DEFAULT_RETRYABLE_STATUS_CODES,
    defaultHeaders: { ...(options.defaultHeaders ?? {}) },
    fetch: fetchImpl,
  };
  hideCredential(config, "apiKey", apiKey);
  hideCredential(config, "accessToken", accessToken);
  return config;
}

/**
 * Store a credential as a non-enumerable property so `JSON.stringify`, `console.log`
 * and `util.inspect` never print it.
 */
export function hideCredential(config: NovaConfig, key: "apiKey" | "accessToken", value: string | undefined): void {
  Object.defineProperty(config, key, { value, writable: true, enumerable: false, configurable: true });
}

/** Default headers for the current authentication and tenant context. */
export function buildHeaders(config: NovaConfig): Record<string, string> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    "User-Agent": `Nova-TypeScript-SDK/${VERSION}`,
    ...config.defaultHeaders,
  };
  const credential = cleanCredential(config.apiKey) ?? cleanCredential(config.accessToken);
  if (credential) headers["Authorization"] = `Bearer ${credential}`;
  if (config.tenantId) headers["X-Tenant-ID"] = config.tenantId;
  return headers;
}
