# Error handling

Every failure is a subclass of `NovaError` (identical names in both SDKs).

| Error | Cause |
|---|---|
| `NovaValidationError` | HTTP 400, or input rejected client-side before any request is sent |
| `NovaAuthenticationError` | 401 |
| `NovaPermissionError` | 403 |
| `NovaNotFoundError` | 404 |
| `NovaRateLimitError` | 429; `retry_after` / `retryAfter` holds seconds from `Retry-After` |
| `NovaServerError` | 5xx |
| `NovaAPIError` | any other 4xx; base class of the HTTP errors above |
| `NovaRedirectError` | unexpected 3xx (never followed) |
| `NovaTimeoutError`, `NovaConnectionError` | network layer |
| `NovaAbortError` (TypeScript) | caller cancelled via `AbortSignal` |

Each error carries `status_code`/`statusCode`, `error_code`/`errorCode` (e.g. `VALIDATION_ERROR`), `details`
(field-level errors for validation failures) and `correlation_id`/`correlationId`; quote the correlation ID when
contacting support.

## Wire format

Errors normally arrive as

```json
{ "success": false, "message": "name: This field is required.", "data": null,
  "error": { "code": "VALIDATION_ERROR", "message": "…", "details": { "name": ["This field is required."] } },
  "meta": { "correlation_id": "…" } }
```

The SDKs also understand the legacy shapes some endpoints still emit (`{"error": "…"}`, `{"detail": "…"}`,
DRF field dictionaries, JSON arrays) and summarise HTML/text bodies from proxies. Credentials, request bodies and
authorization headers never appear in messages.

## Retries

Only `GET`/`HEAD`/`OPTIONS` are retried automatically — on 429, 502, 503, 504, connection failures and timeouts —
with exponential backoff and jitter; `Retry-After` is honoured and capped at 30 seconds. `POST`, `PUT`, `PATCH`
and `DELETE` are **never** retried, because a lost response does not mean a lost request (an email may already be
queued). After a failed dispatch, inspect the delivery logs before retrying yourself.
