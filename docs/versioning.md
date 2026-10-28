# Versioning and compatibility

## Policy

- **API:** the REST API is versioned in the path (`/api/v1`). Within `v1`, changes are additive; a breaking change
  ships as `/api/v2`, and SDKs for it get a new major version.
- **SDKs:** [Semantic Versioning](https://semver.org/), versioned independently per language. Tags:
  `python-vX.Y.Z`, `typescript-vX.Y.Z`. `CHANGELOG.md` in each SDK directory records every release.
- **Generated models are tolerant:** Python models make every field optional and keep unknown fields in `raw`, so a
  newer server never breaks an older SDK. TypeScript types describe the contract at release time; extra fields
  at runtime are preserved.
- **Deprecations:** a deprecated method keeps working for at least one minor release and is announced in the
  changelog before removal in the next major.

## Compatibility matrix

| SDK | Version | Nova API | Contract (`openapi/nova-api.yaml`) | Runtime |
|---|---|---|---|---|
| Python | 0.2.x | `/api/v1` | 1.0.0 | Python 3.10 – 3.14 |
| Python | 0.1.x | `/api/v1` | pre-contract | Python 3.10 – 3.14 |
| TypeScript | 0.1.x | `/api/v1` | 1.0.0 | Node.js 18.17+ (CI: 20/22/24 full suite, 18.17 smoke test) |
| Java | 0.1.x | `/api/v1` | 1.0.0 | Java 17+ (CI: JDK 17 and 21) |

## Feature matrix

| Capability | Python | TypeScript | Java |
|---|---|---|---|
| API key / bearer token auth | ✔ | ✔ | ✔ |
| Tenant header (default + per call) | ✔ | ✔ | ✔ (`withTenant`, `with(RequestOptions)`) |
| Typed responses | ✔ (dataclass models) | ✔ (generated interfaces) | ✔ (generated records) |
| Sync API | ✔ | n/a (promises) | ✔ |
| Async API | ✔ (`AsyncNovaClient`) | ✔ | ✘ (blocking calls; use virtual threads or an executor) |
| Auto-pagination | ✔ `iter_items` / `iter_pages` | ✔ `for await` on `Page` | ✔ `for` / `stream()` on `Page` |
| Multipart upload | ✔ | ✔ | ✔ |
| CSV export | ✔ | ✔ | ✔ |
| Registration / password recovery | ✔ | ✔ | ✔ |
| Retries (idempotent only) | ✔ | ✔ | ✔ |
| `Retry-After` handling | ✔ | ✔ | ✔ |
| Timeouts | ✔ | ✔ | ✔ (connect + request) |
| Cancellation | task cancellation | `AbortSignal` | thread interrupt |
| Correlation IDs | ✔ | ✔ | ✔ |
| Contract coverage | 98/98 required operations | 98/98 required operations | 98/98 required operations |
| Browser / Android use | n/a | browser not supported (opt-in `dangerouslyAllowBrowser`) | Android not a supported target |

Coverage is measured by `scripts/check_sdk_coverage.py`.

## Verification

How each behaviour is checked, and what is *not* checked, is in [verification-plan.md](verification-plan.md) and
[verification-report.md](verification-report.md). In short: per-SDK unit and property tests, a contract-alignment test,
a cross-language conformance suite against a real local HTTP server, and (on demand) mutation testing. None of these
exercises the live Nova backend.

## Known limitations

- No automatic JWT refresh (explicit `refresh` call).
- The Java SDK has no async API and holds uploads in memory.
- No package of any SDK has been published; distribution will use Google Cloud Artifact Registry (see [distribution](distribution.md)).
- Email-log mutation endpoints (create/update/delete) are intentionally not exposed; they are system records.
- Some backend endpoints still return non-enveloped error bodies; SDKs parse them, but `details` can be sparse.
- Integration tests against a running Nova instance are not part of CI yet; unit tests use mocked HTTP and the backend
  repository's contract tests validate real responses against the spec.
