# Nova Java SDK

Official Java client for **Nova — Dynamic Email Template & Email Delivery Platform**.

- Java **17+**, one runtime dependency (`jackson-databind`); HTTP uses the JDK's built-in `java.net.http.HttpClient`.
- Immutable, thread-safe client; typed `record` models and fluent request builders; auto-paginating results.
- Same behaviour as the Python and TypeScript SDKs: API key / bearer auth, tenant header, bounded retries for
  idempotent calls only, `Retry-After`, no redirect following, typed errors, secret redaction.

> **Not published yet.** The SDK is built and tested locally only. Packages will be distributed through a private
> Google Cloud Artifact Registry Maven repository; no release exists and none has been configured.

## Build and install locally

```bash
cd sdks/java
mvn verify                 # compile, test, coverage check, checkstyle, jar + sources + javadoc
mvn install                # installs into your local ~/.m2 only (not a publish)
```

```xml
<dependency>
  <groupId>com.infimatrix</groupId>
  <artifactId>nova-sdk</artifactId>
  <version>0.1.0</version>
</dependency>
```

## Quick start

```java
import com.infimatrix.nova.NovaClient;
import com.infimatrix.nova.Page;
import com.infimatrix.nova.Query;
import com.infimatrix.nova.models.Contact;
import com.infimatrix.nova.models.SendEmailRequest;

NovaClient nova = NovaClient.builder()
        .baseUrl("https://nova.example.com")
        .apiKey(System.getenv("NOVA_API_KEY"))
        .tenantId("00000000-0000-0000-0000-000000000001")
        .build();

var email = nova.emails().send(SendEmailRequest.builder()
        .recipientEmail("ada@example.com").subject("Welcome!").htmlContent("<h1>Hello Ada</h1>").build());
System.out.println(email.messageId() + " " + email.status());

Page<Contact> page = nova.contacts().list(Query.builder().search("acme").pageSize(50).build());
for (Contact contact : page) {        // walks every page, fetching lazily
    System.out.println(contact.email());
}
```

Use the SDK from server-side code. API keys and tokens are secrets and must not be shipped in client applications
(for example Android apps); Android is **not** a supported target of this artifact.

## Configuration

| Builder method | Default | Description |
|---|---|---|
| `baseUrl` | env `NOVA_BASE_URL`, else `http://localhost:8000` | API origin; a trailing `/api/v1` is stripped |
| `apiKey` | env `NOVA_API_KEY` | `nova_key_…`; wins over `accessToken` |
| `accessToken` | env `NOVA_ACCESS_TOKEN` | JWT access token |
| `tenantId` | env `NOVA_TENANT_ID` | default `X-Tenant-ID` |
| `connectTimeout` | 10 s | connect timeout (ignored with a custom `HttpClient`) |
| `requestTimeout` | 30 s | per-attempt timeout |
| `maxRetries` | 3 | retries of `GET` requests (0–10) |
| `retryBackoff` / `retryJitter` | 500 ms / true | exponential backoff base |
| `defaultHeader(name, value)` | – | added to every request |
| `httpClient` | JDK client | bring your own (proxy, TLS); it must use `Redirect.NEVER` |

Clients are immutable. Derive variants instead of mutating: `withTenant(id)`, `withAccessToken(token)`,
`withApiKey(key)`, and `with(RequestOptions)` for tenant, headers, correlation id or timeout of every call made
through the returned client. Variants share the connection pool.

```java
String token = nova.auth().login("ada@example.com", "secret").access();
NovaClient session = nova.withAccessToken(token);
session.withTenant(otherTenant).templates().list(Query.empty());
nova.with(RequestOptions.builder().correlationId("req-42").build()).health();
```

## API map

`auth()` (+`apiKeys()`), `users()`, `tenants()` (+`memberships()`), `templates()`, `contacts()` (+`groups()`),
`emails()`, `providers()`, `webhooks()`, `campaigns()`, `analytics()`, `audit()`, `assets()` (`folders()`, `files()`),
`health()`. Every documented Nova operation is covered except the email-log mutation endpoints
(see `openapi/sdk-exclusions.yaml`). Filters and sorting use `Query`:
`Query.builder().search("x").ordering("-created_at").page(2).pageSize(50).param("status", "ACTIVE").build()`.

Models keep the API's field names through `@JsonProperty` and expose camelCase accessors
(`contact.firstName()`); enum-like fields are `String`s with constants such as `TenantStatusEnum.ACTIVE`, so values
added by a newer server never break parsing. Unknown JSON properties are ignored.

## Pagination

List methods return `Page<T>`: `items()`, `pagination()`, `hasNext()`, `nextPage()`, `pages()`, `stream()`, `toList()`.
Iterating the page walks all following pages lazily.

## Uploads and downloads

```java
nova.assets().files().upload(FileUpload.of(Path.of("logo.png")), folderId);
nova.assets().files().upload(FileUpload.of(bytes, "banner.jpg"), null);
nova.contacts().bulkUpload(FileUpload.of(Path.of("contacts.csv")));
String csv = nova.emails().exportCsv(Query.builder().param("status", "FAILED").build());
```

Uploads are held in memory; very large files are not streamed.

## Errors

All exceptions are unchecked and extend `NovaException` (`statusCode()`, `errorCode()`, `details()`, `correlationId()`).

| Exception | Cause |
|---|---|
| `NovaClientValidationException` | input rejected by the SDK before sending |
| `NovaValidationException` | HTTP 400 |
| `NovaAuthenticationException` | 401 |
| `NovaPermissionException` | 403 |
| `NovaNotFoundException` | 404 |
| `NovaRateLimitException` | 429 (`retryAfter()`) |
| `NovaServerException` | 5xx |
| `NovaRedirectException` | unexpected 3xx (never followed) |
| `NovaTimeoutException`, `NovaConnectionException` | network layer |
| `NovaAbortedException` | the calling thread was interrupted (interrupt flag is preserved) |

## Reliability and security

- Only `GET` is retried (429/502/503/504, connection failures, timeouts) with exponential backoff, jitter and
  `Retry-After` capped at 30 s. `POST`/`PATCH`/`DELETE` are never retried, so a timeout cannot send an email twice.
- Redirects are never followed; credentials are not forwarded to another host.
- Credentials never appear in `toString()`, exception messages or logs. The only logging is a `System.Logger`
  warning (`com.infimatrix.nova.http`) with method, endpoint template and status when a retry happens.
- Path identifiers are percent-encoded and validated; hostile ids cannot alter the request path.

## Design decisions

- **Java 17**: records, `java.net.http`, `HttpClient` thread safety, and long-term support; Jackson 2.22 supports records.
- **JDK HTTP client** instead of OkHttp/Apache: no extra dependency, HTTP/2 over TLS, per-request timeouts, supports
  custom proxies/TLS through `httpClient(...)`.
- **Jackson** for JSON: the de-facto standard, record support, tolerant of unknown properties.
- **Own generator** (`scripts/gen_java_models.py`) rather than a general OpenAPI Generator: the transport,
  authentication, retries and errors are deliberately hand-written to behave exactly like the other SDKs, and only models
  are generated. This is the same hybrid approach as the Python and TypeScript SDKs and keeps the dependency set empty.

## Development

```bash
python scripts/gen_java_models.py           # regenerate models after the OpenAPI snapshot changes
python scripts/gen_java_models.py --check   # CI: fail if committed models are stale
cd sdks/java && mvn verify                  # tests (JDK mock HTTP server), jacoco >= 85% on hand-written code, checkstyle
python scripts/check_sdk_coverage.py --sdk java --strict
```

`ContractTest` calls every SDK operation against a local server and validates each request (method, path,
documented query parameters, content type, required body fields) against `openapi/nova-api.yaml`.

## License

MIT, see [LICENSE](LICENSE).
