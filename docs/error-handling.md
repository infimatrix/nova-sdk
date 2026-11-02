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

## Things that look like errors but are server behaviour

* **A write that references something you just created can fail once.** On the development server used for testing,
  `POST /campaigns/transactional/` with a `template_id`, or a file upload with a `folder`, created moments earlier, answered
  `400 Invalid pk "…" - object does not exist` and succeeded 0.5-2.5 seconds later. The SDKs never retry a 400 or any
  non-idempotent request; if your code creates an object and immediately references it, retry that second call yourself
  after a short pause (and give up after a few seconds).
* **"Queued" is not "delivered".** `emails.send`, `bulk_send`, `group_send` and the test-send calls return as soon as the
  server accepts the mail (status `PROCESSING`). Delivery happens afterwards: without a configured, active mail provider
  the mail ends `FAILED` in the email logs. Create a provider (`providers.create`) first and check `emails.list_logs()`.
* **Some endpoints need a higher role.** For example `users.list` answers 403 for a workspace administrator that is not a
  platform administrator. That is a `NovaPermissionError`, not a bug in the SDK.
* **A failed login answers 400**, so it surfaces as `NovaValidationError`, not `NovaAuthenticationError` (401 is used for
  bad or expired credentials on other endpoints).
* **Secrets are shown once.** A webhook's signing secret is returned by `webhooks.create` (`secret`) and
  `webhooks.rotate_secret`; the raw API key is returned only by `auth.create_api_key`. Store them immediately.
