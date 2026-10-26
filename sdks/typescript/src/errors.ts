/**
 * Typed error hierarchy.
 *
 * Every error thrown by the SDK extends {@link NovaError}. Messages and string forms
 * never contain credentials, authorization headers, or request bodies.
 */

export interface NovaErrorOptions {
  statusCode?: number;
  errorCode?: string;
  details?: unknown;
  correlationId?: string;
  cause?: unknown;
}

/** Base class for every error raised by the Nova SDK. */
export class NovaError extends Error {
  /** HTTP status code, when the error originated from an API response. */
  readonly statusCode?: number;
  /** Machine-readable error code (API-provided, or an SDK code such as `CONNECTION_ERROR`). */
  readonly errorCode: string;
  /** Structured error details, e.g. field-level validation errors. */
  readonly details: unknown;
  /** Correlation ID for support and log tracing. */
  readonly correlationId?: string;

  constructor(message: string, options: NovaErrorOptions = {}) {
    super(NovaError.format(message, options), { cause: options.cause });
    this.name = new.target.name;
    this.statusCode = options.statusCode;
    this.errorCode = options.errorCode ?? "SDK_ERROR";
    this.details = options.details ?? {};
    this.correlationId = options.correlationId;
    this.rawMessage = message;
  }

  /** The message without the `(status=…, code=…)` suffix. */
  readonly rawMessage: string;

  protected static format(message: string, options: NovaErrorOptions): string {
    const meta: string[] = [];
    if (options.statusCode) meta.push(`status=${options.statusCode}`);
    if (options.errorCode) meta.push(`code=${options.errorCode}`);
    if (options.correlationId) meta.push(`correlation_id=${options.correlationId}`);
    return meta.length ? `${message} (${meta.join(", ")})` : message;
  }
}

/** A network, DNS, or socket failure. */
export class NovaConnectionError extends NovaError {
  constructor(
    message = "Failed to establish network connection to Nova API.",
    options: NovaErrorOptions = {},
  ) {
    super(message, { ...options, errorCode: "CONNECTION_ERROR" });
  }
}

/** The request exceeded the configured timeout. */
export class NovaTimeoutError extends NovaError {
  constructor(message = "Request to Nova API timed out.", options: NovaErrorOptions = {}) {
    super(message, { ...options, errorCode: "REQUEST_TIMEOUT" });
  }
}

/** The request was cancelled through the caller's `AbortSignal`. */
export class NovaAbortError extends NovaError {
  constructor(message = "Request was aborted.", options: NovaErrorOptions = {}) {
    super(message, { ...options, errorCode: "REQUEST_ABORTED" });
  }
}

/** Base class for HTTP 4xx/5xx responses (and for client-side validation failures). */
export class NovaAPIError extends NovaError {}

/** The API returned an unexpected 3xx redirect. Redirects are never followed. */
export class NovaRedirectError extends NovaAPIError {
  readonly location?: string;

  constructor(
    message = "Unexpected redirect received from Nova API.",
    options: NovaErrorOptions & { location?: string } = {},
  ) {
    super(message, {
      statusCode: 301,
      ...options,
      errorCode: options.errorCode ?? "UNEXPECTED_REDIRECT",
    });
    this.location = options.location;
  }
}

/** HTTP 401: missing, invalid, or expired credentials. */
export class NovaAuthenticationError extends NovaAPIError {}

/** HTTP 403: authenticated but not permitted. */
export class NovaPermissionError extends NovaAPIError {}

/** HTTP 404: resource not found. */
export class NovaNotFoundError extends NovaAPIError {}

/** HTTP 400, or a request rejected by the SDK before it was sent. */
export class NovaValidationError extends NovaAPIError {}

/** HTTP 429: rate limit exceeded. */
export class NovaRateLimitError extends NovaAPIError {
  /** Seconds to wait before retrying, from the `Retry-After` header. */
  readonly retryAfter?: number;

  constructor(
    message = "Rate limit exceeded.",
    options: NovaErrorOptions & { retryAfter?: number } = {},
  ) {
    super(message, {
      statusCode: 429,
      ...options,
      errorCode: options.errorCode ?? "RATE_LIMIT_EXCEEDED",
    });
    this.retryAfter = options.retryAfter;
  }
}

/** HTTP 5xx: the Nova server failed. */
export class NovaServerError extends NovaAPIError {}

export interface MapApiErrorOptions {
  message?: string;
  errorCode?: string;
  details?: unknown;
  correlationId?: string;
  retryAfter?: number;
  location?: string;
}

/** Map an HTTP status and parsed error body to the matching typed error. */
export function mapApiError(statusCode: number, options: MapApiErrorOptions = {}): NovaAPIError {
  const message = options.message || `API request failed with status ${statusCode}.`;
  const base: NovaErrorOptions = {
    statusCode,
    errorCode: options.errorCode,
    details: options.details,
    correlationId: options.correlationId,
  };

  if (statusCode >= 300 && statusCode < 400) {
    return new NovaRedirectError(message, { ...base, location: options.location });
  }
  switch (statusCode) {
    case 401:
      return new NovaAuthenticationError(message, withCode(base, "API_ERROR"));
    case 403:
      return new NovaPermissionError(message, withCode(base, "API_ERROR"));
    case 404:
      return new NovaNotFoundError(message, withCode(base, "API_ERROR"));
    case 400:
      return new NovaValidationError(message, withCode(base, "API_ERROR"));
    case 429:
      return new NovaRateLimitError(message, {
        ...withCode(base, "RATE_LIMIT_EXCEEDED"),
        retryAfter: options.retryAfter,
      });
    default:
      if (statusCode >= 500) {
        return new NovaServerError(message, withCode(base, "SERVER_ERROR"));
      }
      return new NovaAPIError(message, base);
  }
}

function withCode(base: NovaErrorOptions, fallback: string): NovaErrorOptions {
  return { ...base, errorCode: base.errorCode ?? fallback };
}
