# Conventions every SDK follows

These rules keep the SDKs behaviourally identical while letting each follow its language's idioms.

## Naming

| Concept | Python | TypeScript | Java |
|---|---|---|---|
| Client | `NovaClient`, `AsyncNovaClient` | `NovaClient` | `NovaClient` (immutable) |
| Resources | `client.tenants`, `client.contacts.groups`, `client.audit.access_logs` | `client.tenants`, `client.contacts.groups`, `client.audit.accessLogs` | `client.tenants()`, `client.contacts().groups()`, `client.audit()` |
| Methods | `snake_case` (`list_logs`, `bulk_send`) | `camelCase` (`listLogs`, `bulkSend`) | `camelCase` (`listLogs`, `bulkSend`) |
| Operation verbs | `list`, `get`, `create`, `update` (PATCH), `delete` | same |
| Request/response fields | exactly as in the API (`snake_case`) | exactly as in the API (`snake_case`) | accessors in `camelCase` (`firstName()`); JSON names preserved by `@JsonProperty` |
| Options | `tenant_id=`, `timeout`, `max_retries` | `{ tenantId }`, `timeoutMs`, `maxRetries` | `RequestOptions`, `requestTimeout(Duration)`, `maxRetries` |

Time units follow the language: Python seconds, TypeScript milliseconds (`timeout` vs `timeoutMs`), Java `Duration`.

## Behaviour

| Topic | Rule |
|---|---|
| Base URL | strip trailing `/` and a trailing `/api` or `/api/v1`; only `http`/`https` |
| Headers | `Authorization: Bearer`, `X-Tenant-ID`, `X-Correlation-ID`, `Accept: application/json`, `User-Agent: Nova-<Lang>-SDK/<version>` |
| Credential precedence | API key before access token; `Bearer ` prefixes stripped |
| Envelope | return `data`; keep `meta.correlation_id`; 204/empty bodies → no data; CSV → text; unenveloped JSON → as is |
| Pagination | list methods return a page (`items`, `pagination`, `has_next`/`hasNext`) and accept `page`, `page_size`, `search`, `ordering`; helpers iterate all pages (`iter_items`, `for await`) |
| Retries | idempotent methods only; 429/502/503/504 + connection/timeout; backoff `base·2^attempt` with jitter; `Retry-After` capped at 30 s; `max_retries` 0–10 (default 3) |
| Non-idempotent calls | never retried automatically |
| Redirects | never followed → `NovaRedirectError` |
| Errors | one hierarchy ([error handling](error-handling.md)); unknown 4xx → `NovaAPIError`; client-side input errors → `NovaValidationError` |
| Path ids | validated non-empty and URL-encoded (a hostile id cannot add path segments or query strings) |
| File uploads | multipart field `file`; Python accepts bytes/path/stream, TypeScript Blob/bytes/`{ path }`, Java `FileUpload` (bytes/path/stream) |
| Secrets | never in messages, logs, `repr`/`toString`; TypeScript stores them as non-enumerable properties |
| Dependencies | Python: `httpx` only; TypeScript: none; Java: `jackson-databind` only (JDK HTTP client) |

## Known differences

- Python returns typed model objects that also behave like read-only mappings (backward compatibility with 0.1.x);
  TypeScript returns plain objects typed by generated interfaces.
- TypeScript requests keep API field names in `snake_case`; there is no case-conversion layer.
- Python `with_tenant()` is a sync context manager; TypeScript `withTenant()` returns a new client.
- `PUT` operations are not exposed; `update` always uses `PATCH`.
- Java clients are immutable (`withTenant`, `withAccessToken`, `with(RequestOptions)` return new clients, no setters), `Page` itself
  is `Iterable`, and the Java SDK is blocking-only. Java list filters are passed through `Query` rather than typed per endpoint.
- For a 5xx without an error code, Python and Java report `API_ERROR`; TypeScript reports `SERVER_ERROR`.
