# Nova TypeScript / JavaScript SDK

Official client for **Nova — Dynamic Email Template & Email Delivery Platform**.
Typed, promise-based, zero runtime dependencies. Works with Node.js 18.17+ using the built-in `fetch`.

```ts
import { NovaClient } from "@infimatrix/nova-sdk";

const nova = new NovaClient({
  baseUrl: "https://api.example.com",
  apiKey: process.env.NOVA_API_KEY,
  tenantId: "00000000-0000-0000-0000-000000000001",
});

const email = await nova.emails.send({
  recipient_email: "ada@example.com",
  subject: "Welcome!",
  html_content: "<h1>Hello Ada</h1>",
});
console.log(email.message_id, email.status);
```

## Installation

Distributed through a private Google Cloud Artifact Registry npm repository (not the public npm registry). Map the scope
once in your project's `.npmrc` (no credentials in that file):

```ini
@infimatrix:registry=https://<LOCATION>-npm.pkg.dev/<PROJECT>/<REPOSITORY>/
//<LOCATION>-npm.pkg.dev/<PROJECT>/<REPOSITORY>/:always-auth=true
```

Authenticate with `npx google-artifactregistry-auth` or a short-lived token, then:

```bash
npm install @infimatrix/nova-sdk
```

- Node.js **18.17 or newer** (uses global `fetch`, `FormData`, `Blob`, `AbortController`).
- Ships ESM and CommonJS builds plus TypeScript declarations. No dependencies.

### Browsers

Browsers are **not officially supported**. A Nova API key or access token is a secret that grants
access to your tenant's contacts and the ability to send email on your behalf; any value bundled into
front-end code can be read by every visitor. Call Nova from your server (or a serverless function) and
expose only the results to the browser.

For that reason `new NovaClient({ apiKey })` throws when it detects a browser environment. If you run
in a trusted browser context (for example an internal tool behind SSO) you can opt in with
`dangerouslyAllowBrowser: true`; you accept the risk. Browser CORS configuration is outside this SDK's scope.

## Configuration

| Option | Default | Description |
|---|---|---|
| `baseUrl` | `http://localhost:8000` (env `NOVA_BASE_URL`) | API origin. A trailing `/api/v1` is accepted and stripped. |
| `apiKey` | env `NOVA_API_KEY` | `nova_key_…`; takes precedence over `accessToken`. |
| `accessToken` | env `NOVA_ACCESS_TOKEN` | JWT access token. |
| `tenantId` | env `NOVA_TENANT_ID` | Default tenant sent as `X-Tenant-ID`. |
| `timeoutMs` | `30000` | Per-attempt timeout. |
| `maxRetries` | `3` | Retries of idempotent requests (0–10). |
| `retryBackoffMs` | `500` | Exponential backoff base. |
| `retryJitter` | `true` | Randomise backoff. |
| `defaultHeaders` | `{}` | Added to every request. |
| `fetch` | global `fetch` | Custom implementation (proxy, tests). |
| `dangerouslyAllowBrowser` | `false` | See above. |

Every method accepts a final `RequestOptions` argument:
`{ tenantId, headers, correlationId, signal, timeoutMs }`.

Credentials are stored as non-enumerable properties and redacted by `toString()`, `JSON.stringify` and
`util.inspect`; they never appear in error messages.

## Tenants

```ts
const scoped = nova.withTenant("22222222-…");   // new client, original unchanged (concurrency-safe)
await nova.templates.list({}, { tenantId: "22222222-…" });  // single call
nova.setTenantId("22222222-…");                  // mutates the shared default; avoid in concurrent code
```

## Data model conventions

- Request and response **fields keep the API's `snake_case` names** (`recipient_email`, `page_size`) so
  the types match the API documentation exactly. SDK *option* names are camelCase.
- All model types (`Tenant`, `Template`, `EmailLog`, …) are exported and generated from the OpenAPI contract.
- Methods return the unwrapped `data` payload; use `nova.http.request()` for the full envelope
  (`success`, `message`, `meta`) or `nova.http.requestRaw()` for the raw `Response`.

## Pagination

List methods return a `Page<T>`:

```ts
const page = await nova.contacts.list({ search: "acme", page_size: 50 });
page.items;               // current page
page.pagination.count;    // total items
page.hasNext;

for await (const contact of page) { /* every item on this and all following pages, fetched lazily */ }

const next = await page.getNextPage();   // Page<T> | null
const all = await page.toArray();
```

## Uploads and downloads

```ts
await nova.assets.files.upload({ path: "./logo.png" }, { folder });          // Node: from disk
await nova.assets.files.upload(new Uint8Array(bytes), { filename: "a.png" }); // bytes
await nova.assets.files.upload(new File([blob], "a.png"));                    // Blob/File
await nova.contacts.bulkUpload({ path: "./contacts.csv" });

const csv = await nova.emails.exportCsv({ status: "FAILED" });                // string
const bytes = await nova.emails.exportCsvBytes();                             // Uint8Array
```

## Errors

All errors extend `NovaError` and expose `statusCode`, `errorCode`, `details` and `correlationId`.

| Class | When |
|---|---|
| `NovaValidationError` | HTTP 400, or input rejected by the SDK before sending |
| `NovaAuthenticationError` | 401 |
| `NovaPermissionError` | 403 |
| `NovaNotFoundError` | 404 |
| `NovaRateLimitError` | 429 (`retryAfter` seconds) |
| `NovaServerError` | 5xx |
| `NovaRedirectError` | unexpected 3xx (redirects are never followed) |
| `NovaTimeoutError` / `NovaConnectionError` / `NovaAbortError` | network layer |

```ts
try {
  await nova.templates.get(id);
} catch (error) {
  if (error instanceof NovaNotFoundError) console.warn("missing", error.correlationId);
  else throw error;
}
```

## Reliability

- Only `GET`/`HEAD`/`OPTIONS` are retried automatically (on 429/502/503/504 and network failures),
  with exponential backoff, jitter, and `Retry-After` capped at 30 s.
- `POST`/`PATCH`/`DELETE` are **never retried**, so a timeout can't send an email twice. After a failed
  dispatch, check `nova.emails.listLogs()` before retrying yourself.
- Pass `signal` to cancel a call (including pending retry waits).

## Resources

`auth` (+`apiKeys`), `users`, `tenants` (+`memberships`), `templates`, `contacts` (+`groups`), `emails`,
`providers`, `webhooks`, `campaigns` (+`transactional`), `analytics`, `audit` (+`accessLogs`),
`assets` (`folders`, `files`), plus `health()`. Every documented Nova API operation is covered except
email-log mutation endpoints (see the repository's `openapi/sdk-exclusions.yaml`).

## Compatibility

| SDK | Nova API | Node.js |
|---|---|---|
| 0.1.x | `/api/v1` (OpenAPI 1.0.0) | 18.17, 20, 22+ |

## Development

```bash
npm ci
npm run typecheck && npm test && npm run build && npm run check:package
python ../../scripts/gen_ts_types.py   # regenerate src/schemas.ts after the API contract changes
```
