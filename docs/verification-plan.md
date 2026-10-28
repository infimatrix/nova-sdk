# Verification plan

Passing tests prove that code and tests agree with each other, not that either is right. This plan fixes **where each
expected behaviour comes from** before any new test is written, so a wrong shared assumption can be spotted by a reviewer.

> The article that motivated this approach (`medium.com/@pranavdixit20/…`) returned HTTP 403 to the tooling used for this
> work and could not be read. The plan below follows the principles stated in the task brief instead.

## Sources of truth (in priority order)

| Source | Used for |
|---|---|
| `openapi/nova-api.yaml` (committed snapshot of the backend contract) | paths, methods, parameters, required fields, enums, status codes |
| [conventions.md](conventions.md), [error-handling.md](error-handling.md), [authentication.md](authentication.md) | **client policy** the SDKs promise: headers, credential precedence, retries, redirects, error taxonomy, path-id safety |
| HTTP semantics (RFC 9110) | idempotent methods, `Retry-After` |
| Independently computed values in the test itself | expected URLs, bodies, page sequences are written out literally, never derived by calling SDK code |

Where none of these specifies behaviour, the gap is listed under [Gaps](#gaps) and **no expectation is invented**.

## How each layer is verified

| Layer | Mechanism | What it can show | What it cannot show |
|---|---|---|---|
| Per-SDK unit/mock tests (existing) | pytest / vitest / JUnit | the SDK does what its authors intended | that the intent is right |
| Contract tests (existing, `tests/contract`, Java `ContractTest`) | request shape checked against the OpenAPI document | method/path/query/body-field agreement with the contract | response semantics, retry policy |
| **Cross-language conformance** (`tests/conformance`) | one neutral scenario file, one real local HTTP server, a thin driver per language; expectations come from the docs above | the three SDKs agree with the *documented policy* and with each other, over real sockets | behaviour against the live backend |
| **Property tests** | Hypothesis, fast-check, jqwik | documented invariants over many generated inputs | behaviour the docs do not state |
| **Mutation testing** | mutmut / Stryker / PIT on handwritten transport code | whether the tests *notice* a wrong implementation | that surviving mutants matter (some are equivalent) |
| Live integration | none | — | **NOT VERIFIED** (no backend/credentials used) |

## Behaviour matrix

`C-nn` ids are the conformance scenarios in `tests/conformance/scenarios.json`; each cites its documented source.

| ID | Behaviour | Expected (and source) | Boundary / negative | Other tests that cover it |
|---|---|---|---|---|
| C-01 | Standard headers | `Authorization: Bearer <key>`, `Accept: application/json`, `X-Tenant-ID`, `User-Agent: Nova-<Lang>-SDK/…` (conventions §Behaviour) | tenant header absent when none configured | per-SDK config tests |
| C-02 | Credential precedence | API key wins over access token (authentication §Credentials) | access token alone is used | `test_config`, `config.test.ts`, `ConfigTest` |
| C-03 | `Bearer ` prefix stripped | header is `Bearer <raw>` not `Bearer Bearer <raw>` (authentication) | prefix plus whitespace | same |
| C-04 | Base-URL normalisation | trailing `/`, `/api`, `/api/v1` removed (conventions) | combination `/api/v1/` | `test_config` etc. |
| C-05 | Envelope unwrap | returns `data` of `{success,data,meta}` (conventions §Envelope) | unenveloped JSON returned as is | resource tests |
| C-06 | Empty body | 204 → no data (conventions) | — | resource tests |
| C-07 | Path-id safety | a hostile id never creates an extra path segment or query (conventions §Path ids) | `../x`, `a/b`, `a?b=c`, `a#b`, space, `%2F`, empty | `test_path_ids`, `resources.test.ts`, `ResourcesTest` |
| C-08 | Query encoding | `search` value reaches the server byte-for-byte after standard decoding (RFC 3986) | `&`, `=`, `+`, space, `%`, unicode | pagination tests |
| C-09 | GET retried on 503 | idempotent + 503 retried, success returned (error-handling §Retries) | request count == 2 | `test_retries` etc. |
| C-10 | POST never retried | one request only, error raised (error-handling §Retries) | 503 and 429 on POST/DELETE/PATCH | same |
| C-11 | Retry exhaustion | `max_retries=n` → at most `n+1` requests, last error raised | `max_retries=0` → 1 request | same |
| C-12 | `Retry-After` honoured | a `Retry-After: 0` 429 is retried; value exposed as seconds on the error when not retried (error-handling) | cap 30 s (not run: would need 30 s wall clock; covered by unit tests) | same |
| C-13 | Status → error class | 400 Validation, 401 Authentication, 403 Permission, 404 NotFound, 429 RateLimit, 5xx Server, other 4xx API (error-handling table) | 409, 418, 422 are "other 4xx" | `test_exceptions`, `test_error_bodies` |
| C-14 | Error envelope fields | `code`, `details`, `correlation_id` surfaced (error-handling §Wire format) | legacy `{"detail":…}` / `{"error":…}` bodies still classified by status | `test_error_bodies` |
| C-15 | Redirect | 3xx never followed; Redirect error; exactly one request (authentication §secrets) | 301/302/307/308 | `test_http` etc. |
| C-16 | Malformed success body | HTTP 200 with invalid JSON must **not** look like success | truncated JSON, HTML | `test_http` etc. |
| C-17 | Secret hygiene | the API key never appears in error messages/`str` (authentication §Handling secrets) | server echoes nothing; key with special characters | `test_security`, `config.test.ts`, `ConfigTest` |
| C-18 | Pagination walk | `page`/`page_size` sent; iteration visits pages `1..total_pages` in order, no duplicates or skips (conventions §Pagination) | single page, empty page, `has_next=false` before `total_pages` | `test_pagination`, `pagination.test.ts`, `PaginationTest` |
| C-19 | Per-call tenant override | per-call tenant replaces the default in `X-Tenant-ID` (authentication §Tenancy) | invalid (non-UUID) tenant rejected before any request | config tests |
| C-20 | Connection failure | refused connection → Connection error (error-handling) | GET retried then raised; POST not retried | `test_retries` etc. |
| C-21 | Timeout | slow server → Timeout error, not success | POST not retried | same |
| C-22 | Body serialisation | JSON body has the supplied field values exactly, Unicode intact, `Content-Type: application/json` | quotes, emoji, newline | `ContractTest` etc. |

## Property tests (documented invariants only)

| Language | Invariant | Source |
|---|---|---|
| all | an id containing any characters produces at most one path segment after `templates/` and no query | conventions §Path ids |
| all | any non-empty search string round-trips to the server | RFC 3986 + conventions |
| all | base-URL normalisation is idempotent and never leaves `/api`/`/api/v1`/trailing `/` | conventions |
| all | the API key (random printable string) is absent from every error `str`/`repr`/`toString` | authentication |
| all | pagination over *k* generated pages yields every item once, in order | conventions |

Random seeds are printed (Hypothesis `--hypothesis-show-statistics`/derandomised settings, fast-check `seed`, jqwik `seed`),
so a failure is reproducible.

## Mutation testing

Scope: handwritten transport / config / pagination / error-mapping code (not generated models).
Python: mutmut on `http.py`, `config.py`, `pagination.py`, `exceptions.py`. TypeScript: Stryker on `http.ts`, `config.ts`,
`errors.ts`. Java: PIT on `com.infimatrix.nova.http`, `NovaConfig`, `Page`, `errors`. Results, survivors and the reason for
each important survivor are recorded in [verification-report.md](verification-report.md); a run that is cut short is
labelled as such.

## Gaps

* The contract does not state the maximum page size, the retryable status list, or backoff timings; these are
  client policy (conventions) and tested only for their documented effects (request counts), not for timing.
* The `Retry-After` 30 s cap is not exercised end to end (wall-clock cost); unit tests cover it.
* The contract describes the envelope but the backend can emit legacy error shapes; tests assert classification by
  status, not exact message text.
* Python `templates.create` sends default values (`status: ACTIVE`, empty strings) for omitted fields, TypeScript and
  Java send only supplied fields. Whether the server default and the SDK default must agree is a product decision and is
  reported, not changed.
* No live-backend run: **NOT VERIFIED** against the real Nova service.
