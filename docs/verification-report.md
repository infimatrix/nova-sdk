# Verification report

Status vocabulary: **PASS** executed and passed, **FAIL** executed and failed, **NOT RUN** not executed,
**NOT VERIFIED** the evidence available cannot establish the claim. Results below come from command exit codes and
output, produced on 2026-10-26/28 on one Linux workstation (Python 3.14.4, Node 20.20 and 22.23, JDK 17.0.21,
Maven 3.9.9). The plan this report answers is [verification-plan.md](verification-plan.md).

**This report does not say the SDKs are production-ready.** It says what was checked, what the checks found, and what
nobody has checked yet (see [Not verified](#not-verified)). The automated checks in sections 2-10 never touched a live Nova backend; section 12 reports a separate manual end-to-end run against a development server.

## 1. Summary

| | |
|---|---|
| Baseline before any change | all existing checks PASS (Python 317 tests, TypeScript 115, Java 84, contract 34, coverage 98/98 each) |
| Final, from a clean copy of the tree (`scripts/verify_all.sh`) | **40 PASS, 0 FAIL, 0 NOT RUN** |
| Defects found in existing SDK code | **3** by the conformance and mutation work (path ids, invalid JSON body, redirect credentials) plus **3** by the live run (tenant id demanded, Python list paging, response fields lost); all fixed, each with regression tests |
| Test-suite weaknesses found by mutation testing | retry timing, `Retry-After`, 3xx/2xx boundaries and error-field propagation were not pinned; now covered |
| Injected defects detected by the cross-language suite | 28 of 28 (plus 3 equivalent ones masked by a second layer); 31 defects in total across the three SDKs |
| Live end-to-end run of all three SDKs against a development server, with real SES delivery | first run: findings; **after the fixes: 0 FAIL in all three SDKs, 6 of 6 emails DELIVERED per SDK** (section 12) |
| TLS, CodeQL, JDK 21 / Node 18 / Python 3.10-3.13 runs, production backend | **NOT RUN / NOT VERIFIED** (section 11) |

### Defects found in the existing SDKs

| # | Defect | SDKs | Found by | Severity (our judgement) |
|---|---|---|---|---|
| 1 | Path id `.` or `..` is not neutralised: `templates.get("..")` requested `/api/v1/` (HTTP stacks normalise dot-segments); Java sent a raw `..` segment. Contradicts "a hostile id cannot add path segments" ([conventions](conventions.md)). `templates.delete(".")` would address the collection URL. | Python, TypeScript (exact), Java (raw segment) | conformance suite, scenario C-07a | low-medium: needs a caller-controlled id |
| 2 | A 2xx response declaring `application/json` with an invalid body was returned as success text: Python and TypeScript handed a string back typed as a model; Java only failed by accident in model deserialisation. | all three | conformance suite, C-16a | medium: false success |
| 3 | Credentials were not fully stripped from a redirect `Location` whose password contains `@` (`http://user:se@cret@host/`): Python reported `http://cret@host/...`, Java reported the whole URL including `user:se@cret@`. TypeScript was correct. | Python, Java | mutation testing (surviving `rsplit` mutant), then conformance C-15c | low: the value is the server's own header, but it contradicts [authentication](authentication.md) |

Fixes: commits `b3c09d5` and `6c67ed1` (see section 14). Each fix has a unit test that fails on the previous source; this was
checked by running the new tests against a clean worktree of the commit before the fix (Python 3 failures, TypeScript 3,
Java 4 for defects 1-2) and, for defect 3, by the conformance scenario failing for Python and Java before the fix.

### Mistakes made while writing the new tests (and how they were caught)

Recorded because the point of this exercise is that tests can share the author's wrong assumption.

* A Python fix used `NovaAPIError` without importing it. Ruff and mypy flagged it, and the conformance suite crashed on it;
  **none of the 317 existing unit tests reach that branch**.
* A unit test asserted that a literal id `%2e%2e` is rejected. Wrong: it is data, is encoded to `%252e%252e`, and must be
  sent. Corrected to assert that.
* A TypeScript test assumed `Retry-After: 0` waits 50 ms (copied from the backoff floor). RFC 9110 says zero means retry
  now, and Python agrees; expectation corrected.
* The first version of the pagination scenario required the first request to carry `page=1`. The docs do not say that;
  the scenario was loosened to what is documented.
* The first injected "backoff" defect (`attempt + 1` instead of `2 ** attempt`) was undetected because the scenario had only
  two retries, where both formulas give 1 and 2. The scenario now uses three retries.

## 2. Baseline

Recorded before any change, in clean environments:

| Check | Result |
|---|---|
| Python: ruff, ruff format, mypy, pytest | PASS, 317 tests |
| TypeScript: typecheck, vitest, build, check:package, `npm audit --omit=dev` | PASS, 115 tests, 0 vulnerabilities |
| Java: `mvn verify` (tests, JaCoCo gate, Checkstyle, javadoc, jar) | PASS, 84 tests |
| Root: contract/alignment tests, 4 generator `--check`, coverage `--strict` | PASS, 34 tests, 98/98 operations for each SDK |
| Known failures | none |

The Java SDK already existed in the repository (`sdks/java`, 0.1.0) when this work started, so it was audited and hardened
rather than recreated. The generator is the repository's own `scripts/gen_java_models.py` (documented in
[sdks/java/README.md](../sdks/java/README.md)); the pre-existing decision not to use OpenAPI Generator was kept.

## 3. Test results (clean copy, final code)

`scripts/verify_all.sh` copies the tracked and new files to a scratch directory, creates fresh virtualenvs and
`node_modules`, and uses a throw-away Maven repository. Output: 40 PASS.

| Area | Check | Result |
|---|---|---|
| Root | contract + conformance-checker tests (`pytest tests`) | PASS, 68 tests (42 contract incl. overlay and release-safeguard cases, 26 checker) |
| Root | generated code up to date (python models, python async, ts types, java models) | PASS x4 |
| Root | SDK coverage of the contract, strict | PASS: python, typescript, java each 98/98 required operations (4 documented exclusions in `openapi/sdk-exclusions.yaml`) |
| Root | actionlint on all workflows; YAML parse | PASS; PASS |
| Python | ruff check / format / mypy | PASS x3 |
| Python | pytest (unit + property) | PASS, 365 tests |
| Python | sdist + wheel build, `twine check` | PASS |
| Python | wheel and sdist install into clean venvs; import smoke test run outside the source tree | PASS x3 (prints `0.2.0`) |
| TypeScript | `npm ci`, typecheck, vitest (unit + property), build, `check:package` | PASS, 160 tests in 9 files |
| TypeScript | `npm pack`, tarball install into a clean project, ESM import, CJS require | PASS x4 (prints `0.1.0`) |
| Java | `mvn clean verify` (tests, JaCoCo, Checkstyle, javadoc, jar, sources) | PASS, 115 tests, 0 Checkstyle violations |
| Java | install into a throw-away local Maven repo + separate consumer project compiles and runs | PASS x2 |
| Cross-language | `tests/conformance/conformance.py` | PASS, 351/351 (117 scenarios x 3 SDKs) |

Only the local Python (3.14), Node (20/22) and JDK (17) versions were exercised here. The CI matrices (Python 3.10-3.14,
Node 18.17/20/22/24, JDK 17/21) are defined in the workflows but were **NOT RUN** for this report.

## 4. Independent contract and alignment tests

| Test | What it checks | Source of expectations | Result |
|---|---|---|---|
| `tests/contract/*` (pre-existing) | snapshot valid OpenAPI, envelope/auth/tenant/pagination rules, SDK alignment, release safeguards | the OpenAPI snapshot and documented rules | PASS |
| Java `ContractTest` (pre-existing) | every SDK operation's method, path, documented query parameters, content type and required body fields against `openapi/nova-api.yaml` | the OpenAPI document | PASS |
| `check_sdk_coverage.py --strict` | each SDK calls every required operation and none that do not exist | the OpenAPI document | PASS 98/98 x3 |

Limit: these check request shape, not response semantics, retries or error policy. Those are covered by the conformance
suite below. `info.version` of the contract and the SDK package versions are tracked separately ([versioning](versioning.md)).

## 5. Cross-language conformance

`tests/conformance/` runs one neutral scenario file against a real local HTTP server and a thin driver per SDK
([README](../tests/conformance/README.md)). 117 scenarios expand to 351 runs. Every scenario cites its documented source
in its `doc` field. Result: **PASS 351/351**. Scenarios C-23 (tenant lookup, tenant paging) and C-24 (typed render and webhook-secret fields) were added after the live run.

| Behaviour (verification-plan ids) | Scenarios | Notes |
|---|---|---|
| Standard headers, credential precedence, `Bearer ` stripping (C-01..03) | 6 | |
| Base URL normalisation (C-04) | 6 variants | `/`, `/api`, `/api/v1` and slashes |
| Envelope, unenveloped JSON, 204 (C-05, C-06) | 3 | |
| Hostile path ids (C-07) | 15 + 2 empty | judged by an invariant: rejected, or one encoded non-dot segment that round-trips |
| Query encoding (C-08) | 10 values | `& = + % space unicode # ?` |
| Retry policy (C-09..C-12) | GET retried on 502/503/504/429; POST/DELETE never; exhaustion; `max_retries=0`; `Retry-After` waited on | timing measured from server arrival times (backoff 100/200/400 ms; 1 s `Retry-After`) |
| Status to error class (C-13), error fields for every class (C-14) | 12 + 9 | code, details, correlation id propagate for 400/401/403/404/409/418/429/500/503 |
| Redirects (C-15) | 300, 301, 302, 303, 304, 307, 308, 399 not followed; 2xx boundary 200..299; credentials stripped from `Location` | |
| Malformed JSON success (C-16), secret redaction (C-17) | 2 | |
| Pagination (C-18) | page params, walk all pages, empty page, stop when `next` is null | |
| Tenant override and validation (C-19), connection refused and timeout with SDK codes (C-20, C-21), body serialisation (C-22) | 7 | |

The suite itself is tested: `tests/conformance/test_checker.py` (26 tests) feeds the checker wrong observations (wrong
header, extra retry, leaked secret, wrong timing window, hostile path) and requires a violation for each.

### Defect injection ("would a plausible wrong implementation pass?")

`tests/conformance/inject_defects.py` copies each SDK, applies a one-line representative bug, rebuilds, and runs the
suite against that copy only. Final result on the final code: **28 detected, 3 equivalent, 0 missed** (31 defects; the 6 added after the live run target the tenant lookup and deletion).

| Defect (per SDK where listed) | Detected by |
|---|---|
| POST retried automatically (PY, TS, JV) | C-10, C-13, C-14a, C-21 |
| `Authorization` without `Bearer` (PY, TS, JV) | C-01, C-02, C-03 |
| Backoff linear (PY) / shrinking (TS) / 0,1,4 (JV) instead of doubling | C-11c |
| `Retry-After` ignored (PY) / divided (TS) / 1000x too short (JV) | C-12c (and C-12b for JV) |
| HTTP 300 not a redirect, both layers patched (PY, TS, JV) | C-15 |
| Correlation id dropped for 401 (PY) | C-14a |
| Pagination skips every other page (PY, TS, JV) | C-18b |
| Dot-segment guard removed (PY, JV) | C-07a |
| Invalid JSON reported as success (TS) | C-16a |
| HTTP 300 not a redirect in the transport only (PY, TS, JV) | **equivalent**: each SDK maps 3xx in a second place, so the observable behaviour is unchanged |

The earlier run of this tool reported 5 undetected defects; two were weak defects (see section 1), three were the
redundant-layer cases above, and one was a patch that did not match the source. All were resolved as described, none by
removing assertions.

A later full run of the tool on the final code first reported two misses (pagination skipping pages in TypeScript and Java).
The defects were being caught, but a hand-run showed the cause was in the harness: with the defect, the new tenant-paging
scenario made the SDK loop, the driver timed out, and the runner crashed on the unhandled timeout instead of reporting a
failed scenario, so the tool saw no failures. Fixed in the harness (a hung driver is now a reported failure, and the scripted
server stops a request loop after 60 requests), with two checker tests for it; both defects are now detected, by C-18b and
C-23e. No expectation was loosened.

## 6. Property-based tests

Properties are limited to invariants the documentation states; each cites its source in the test.

| SDK | Tool | Properties (examples each) | Result |
|---|---|---|---|
| Python | Hypothesis 6.170 | path id never adds segments/query/dot-segment (200); search value round-trips (200); base URL normalisation stable (200); API key absent from errors and reprs (200); pagination visits every item once in order (200) | PASS |
| TypeScript | fast-check 3.23.2 | same five properties (200 runs each) | PASS |
| Java | jqwik 1.10.2 | same five properties (60-150 tries each) | PASS |

Reproducibility: Hypothesis prints a reproduction blob and `--hypothesis-seed`; fast-check prints seed and path; jqwik
prints the seed (database in `target/`, not committed). The properties passed on the first run; their ability to fail is
supported by the mutation results and by the injected path-id defect (PY-8, JV-7) which the suite catches.

Not covered by properties: whitespace handling of ids can differ between languages for exotic characters (Python `str.strip`,
JavaScript `trim` and Java `String.strip` use different definitions of whitespace, for example for U+00A0 and U+FEFF;
reasoned from the language documentation, **not tested**). The docs only say "non-empty", so no
expectation was invented ([Open questions](#13-open-questions-needing-a-decision)).

## 7. Mutation testing

Scope: handwritten transport, configuration, pagination and error-mapping code. Generated models are excluded (they are
reproduced by `gen_*.py --check`). Scripts: [scripts/mutation/](../scripts/mutation/README.md).
Scores are **evidence of test sensitivity, not a correctness percentage**; "killed %" counts killed plus timeout.

| SDK | Tool and version | Scope | Mutants | Before (existing tests + first new tests) | After (all new tests, before defect 3 fix) |
|---|---|---|---|---|---|
| Java | PIT 1.30.1 + pitest-junit5-plugin 1.2.3 | `http.*`, `NovaConfig`, `Page*`, `Query*`, `errors.*`, `Validate` | 384 | 313 killed (81.5%), 57 survived, 14 no coverage | 325 killed (84.6%), 45 survived, 14 no coverage |
| TypeScript | StrykerJS 10.1.1 (Node 22) | `http.ts`, `config.ts`, `errors.ts`, `models.ts` | 837 | 591 killed (70.6%), 211 survived, 35 no coverage | 607 killed (72.5%), 199 survived, 31 no coverage |
| Python | mutmut 3.8.0 (pytest 9.1.1) | `http.py`, `config.py`, `pagination.py`, `exceptions.py` | 1070 | 587 killed (54.9%), 482 survived, 1 not finished | 638 killed (59.6%), 432 survived |

"Before" is the state with the original tests plus the first batch of new regression/property tests; "after" adds the
retry-delay, boundary and override tests. Each tool was run once per state (no repeated runs, so no variance estimate).
The "after" runs predate the redirect-credential fix (defect 3), which the surviving Python mutant had pointed to.

What the survivors showed, and what was done:

* **Retry delay arithmetic, `Retry-After` waiting and its 30 s cap, 3xx/2xx boundaries, per-request headers and `allow_retry`
  overrides were not pinned in any SDK** (retry counts were). Tests added in all three (`test_retry_delays.py`,
  `retry-delays.test.ts`, `RetryAndFormatTest`) and mirrored in the conformance suite.
* Java: empty-body handling, exception message format, config redaction boundaries, multi-placeholder paths and the
  pagination stop condition were pinned by new tests (`RetryAndFormatTest`).
* **Python redirect sanitiser**: a surviving `split("@", 1)` -> `rsplit` mutant led to defect 3.
* Remaining survivors are mostly not behaviour: Python's 432 break down (heuristic classification of the mutation diff, may
  misfile some) into about 166 string-literal or case changes (messages, log text, default code strings), 59 condition or
  boundary changes inside HTML/text sanitising helpers, 42 dropped exception or envelope fields (`message=None`, `meta=None`),
  2 logging calls, and 163 unclassified (for example `lstrip(None)`, `or True` in branches that other checks make
  equivalent, header-name case changes, which are equivalent because HTTP header names are case-insensitive).
  Not every one of these was reviewed individually; the **42 dropped-field and 59 sanitiser survivors are the ones most
  worth a future pass**. TypeScript survivors are similar: error-class default messages and codes (`errors.ts` has the
  lowest score, 50% before), log strings, and error-body parsing branches for legacy shapes.
* Equivalent mutants (for example percent-encoding an unreserved character in Java `encodeSegment` boundaries, header-name
  case, `Math.max(50, ...)` clamps on already-large values) were not individually excluded; the totals include them.
* One Python mutant timed out and one earlier run left a mutant unfinished; both are counted as above.

Limits: mutation tools only create the mutants they know; they cannot find a missing behaviour. A mutant that survives in
`sanitize_error_text` can be harmless or a leak. Neither a high nor a low score substitutes for the traceability above.

## 8. Static analysis, secrets and dependencies

| Check | Tool | Result |
|---|---|---|
| Python static security | bandit 1.9.4 (`-ll`: medium and high fail) over SDK source, scripts and the conformance harness | PASS. Low-severity notes only: `random` used for retry jitter (not security relevant), `subprocess` in dev scripts. One medium (B310, `urlopen` in `sync_openapi.py`) was a false positive: the code only opens `https://` URLs and refuses `http://`; annotated `# nosec B310` with the reason |
| Secrets, history and tree | gitleaks 8.30.1 (pinned, sha256 verified), the full git history | PASS with `.gitleaks.toml`. Without the allowlist: 13 findings in the tree, all synthetic fixtures (`nova_key_test…`, `nova_key_TOPSECRET…`, patterned `whsec_…`); no real credential found. The allowlist lists those fixture patterns only. `AKIA…EXAMPLE` documentation keys are not flagged |
| Python runtime dependencies | pip-audit on the 7 pinned runtime packages (httpx, httpcore, h11, anyio, idna, certifi, typing_extensions) | PASS, no known vulnerabilities. (An earlier harness version audited the throw-away venv and flagged `pip` itself; that was a harness error, not an SDK dependency.) |
| npm | `npm audit --omit=dev --audit-level=low` (the package has no runtime dependencies) and `npm audit --audit-level=high` for dev tooling | PASS, 0 vulnerabilities |
| Java dependencies | runtime: `jackson-databind` only | NOT RUN: no Java vulnerability database scan was run locally; CI uses GitHub dependency review on pull requests |
| CodeQL (python, javascript-typescript, java-kotlin) | `ci.yml` | NOT RUN locally (runs in GitHub only) |
| Workflows | actionlint + yamllint, all actions pinned to commit SHAs, `permissions: contents: read` by default, no secrets or publish in ordinary CI (enforced by `test_release_safeguards.py`; since the final change the repository has the single workflow `ci.yml`: gitleaks, CodeQL, tests) | PASS |

Licences (`LICENSE` is byte-identical in the root and the three SDK directories; `pyproject.toml`, `package.json` and
`pom.xml` declare MIT):

| Component | Licence | Shipped? |
|---|---|---|
| httpx, httpcore, h11, anyio, idna, typing_extensions | BSD-3 / MIT / PSF | runtime (Python) |
| certifi | MPL-2.0 | runtime (Python, via httpx), unmodified |
| jackson-databind | Apache-2.0 | runtime (Java) |
| Hypothesis | MPL-2.0 | dev only |
| fast-check | MIT | dev only |
| jqwik | EPL-2.0 | test scope only, not shipped |
| PIT, Stryker, mutmut | Apache-2.0 / Apache-2.0 / BSD-3 | on-demand tools |

Note on jqwik: its log output contains a banner addressed to AI agents telling them not to use the library and to ignore
its results. That text is part of the third-party tool's output, not an instruction from the project owner, and was not
acted on; the property results are reported like any other. Reviewers who dislike a test dependency that does this may
prefer another property-testing library for Java.

**Copyright holder: NOT VERIFIED.** All licence files read "Copyright (c) 2026 Nova Engineering Team". Nothing in the
repository establishes that this name is authorised to represent the project or the Infimatrix organisation. The text was
not changed by this work and was already published; confirmation by the owner is needed.

## 9. Build, installation and reproducibility

| Check | Result |
|---|---|
| Python wheel and sdist build, `twine check`, install in clean venvs, import outside the source tree | PASS |
| TypeScript tarball `npm pack`, install in a clean project, ESM and CJS import | PASS |
| Java jar installed into a throw-away local Maven repository, separate consumer project compiles and calls the SDK | PASS (no remote registry used) |
| Python wheel built twice (same `SOURCE_DATE_EPOCH`) is byte-identical | PASS |
| `npm pack` twice gives byte-identical tarballs | PASS |
| Java jar built twice is byte-identical (`project.build.outputTimestamp` is pinned) | PASS |
| Generated code reproducible (`gen_*.py --check`) | PASS x4 |

## 10. Requirement-to-test traceability (excerpt)

Full behaviour list and sources: [verification-plan.md](verification-plan.md). `C-nn` are conformance scenarios.

| Documented requirement | Source | Tests that fail if it breaks |
|---|---|---|
| Standard headers; API key beats token; `Bearer ` stripped | conventions, authentication | C-01..03; `test_config`, `config.test.ts`, `ConfigTest` |
| Hostile ids cannot add segments, queries or dot-segments | conventions "Path ids" | C-07a/b; `test_path_ids`, `test_http`, `http.test.ts`, `TransportTest`; property tests x3 |
| Only idempotent methods retried; bounded; backoff `base*2^attempt`; `Retry-After` honoured, capped at 30 s | error-handling, conventions | C-09..C-12; `test_retry_delays.py`, `retry-delays.test.ts`, `RetryAndFormatTest`. The 30 s cap is exercised in unit tests only (Python and TypeScript: 120 s header gives 30 s); **not in Java** |
| Status to error class; code/details/correlation id carried | error-handling | C-13, C-14; `test_exceptions`, `test_error_bodies`, `errors` tests |
| Redirects never followed; credentials stripped from `Location` | authentication | C-15, C-15c; redirect unit tests in all SDKs |
| A success must not be reported for a broken body | error-handling (client policy) | C-16a; new unit tests in all SDKs |
| Secrets never in messages | authentication | C-17; `test_security`, property tests x3 |
| Pagination walk and stop | conventions | C-18; `test_pagination`, `pagination.test.ts`, `PaginationTest`, property tests |
| Tenant header, override, UUID validation | authentication | C-19; config tests |
| Body serialisation incl. Unicode | OpenAPI | C-22; `ContractTest`, resource tests |

## 11. Not verified

| Area | Status | Why / what would close it |
|---|---|---|
| Behaviour against the **production** backend, other tenants/roles (platform admin), SES production limits | NOT VERIFIED | section 12 covers one development server and one tenant-admin account only |
| TLS certificate verification on by default | NOT VERIFIED | Python's config sets `verify_ssl=True` by default (read, not tested); TypeScript and Java rely on platform defaults; no test serves an invalid certificate |
| Request cancellation (TypeScript `AbortSignal`, Java interrupt, Python task cancel) | NOT RUN | not part of the conformance suite; pre-existing unit tests exist per SDK |
| Multipart uploads, CSV exports, file downloads end to end | NOT RUN here | covered by pre-existing per-SDK tests only |
| Java `Retry-After` 30 s cap | NOT VERIFIED | no test; Python and TypeScript have one |
| CI matrices (Python 3.10-3.13, Node 18.17/20/24, JDK 21), Windows/macOS | NOT RUN | only Python 3.14, Node 20/22, JDK 17 on Linux were available |
| CodeQL, GitHub dependency review, Java dependency vulnerability scan | NOT RUN | run in GitHub only |
| Breaking-change detection between contract versions | NOT RUN | no tool such as oasdiff was added; `sync_openapi.py --check` detects drift only |
| Copyright holder authorisation | NOT VERIFIED | see section 8 |
| Tenant lookup for accounts that belong to several tenants | NOT VERIFIED | only a single-tenant account was available; the SDK uses the tenant the server reports |
| Mutation scores after the second round of changes | NOT RUN | section 7 numbers are from before the tenant-lookup, overlay and paging changes |
| Large responses, high concurrency, memory | NOT RUN | not in scope of local checks |
| Mutation coverage of resources/models | NOT RUN | excluded (generated or declarative) |

## 12. Live end-to-end run against a development server

A manual run, outside CI, on 2026-11-02. The server URL and the account were supplied by the project owner and are not
recorded here (the repository is public). Credentials were passed through environment variables only; nothing secret was
written to a file, the repository or a log, and the output of the scripts was redacted. The scripts are not part of the
repository (they create real data and send real mail); the steps they perform are listed below so the run can be repeated.

**Method.** Phase 1 logs in with email and password and creates an API key. Phase 2 builds a **new client with only the
server URL and that API key (no tenant id)** and exercises every resource. Phase 3 deletes everything the run created,
revokes the key and logs out. A tenant-admin account with one tenant was used. An AWS SES provider
(region ap-south-1, one verified sender) was added to the tenant through `providers.create`, at the owner's request, and was
left in place; emails were sent only to plus-tagged variants of the owner's own address.

**Contract drift check.** `sync_openapi.py --check` against the server's live schema reports all 102 operations as "differs",
but the set of operations is identical (102 vs 102, none added or removed); the differences are descriptions, duplicated
security entries and the wording of some response schemas.

| SDK | Steps | PASS | PASS after retry | FAIL | NOT RUN |
|---|---|---|---|---|---|
| Python | 102 | 102 | 0 | 0 | 0 |
| TypeScript | 101 | 98 | 1 | 2 (the script reported two checks as FAIL because it did not mark the SDK's correct "tenant id required" error as expected; the SDK behaved exactly like Python and Java there, finding L1; the script was corrected afterwards but not re-run) | 0 |
| Java | 100 | 98 | 1 | 1 (`templates.render`, finding L3) | 0 |

(An earlier run before the provider existed gave 91/90/90 passes and left providers and real delivery NOT RUN.)

Covered in every SDK: login, refresh (the server rotates the refresh token), API-key create/list/revoke, `auth.me`, users,
tenants (list, get, create, update, delete, members), templates (create, get, list with search, update, render, activate,
archive, delete), contacts (create, get, search, update, activity, duplicate rejection, CSV sample, bulk upload, groups
create/get/update/list/delete), providers (list, types, get, test, create, update, delete), emails (send, send from a template,
bulk send, group send, logs, preview, CSV export), webhooks (events, create, get, list, update, rotate secret, test, delete),
transactional campaigns (create, get, list, update, test send, delete), analytics, audit logs and stats, asset folders and
files (upload, update, delete), pagination across more than one real page, wrong or revoked API key (401), unknown id (404),
invalid and foreign tenant ids. After the run a server-side audit found **0 leftover test objects** and no active test API keys.

**Email.** With the SES provider in place every email sent by each run (send, send from a template, bulk send, group send,
provider test, campaign test) ended `DELIVERED`: 6 of 6 for each of the three SDKs, asserted by the script after waiting
15 s. Before the provider existed the same calls were accepted by the API and then ended `FAILED`, so the API's "queued"
answer says nothing about delivery. The provider response did not contain the AWS secret access key (asserted); it does
contain the access-key id, which the contract declares.

### Findings from the live run

| # | Finding | Type | Affects |
|---|---|---|---|
| L1 | Setup of only URL + API key works: the server resolves the tenant itself and `auth.me()` returns it. The only calls that still demand a tenant id are the six `/tenants/{tenant_id}/members/...` operations, where all three SDKs raise a client error unless an id is passed. The id is obtainable from `auth.me()` or `tenants.list()`. | design gap | all |
| L2 | **Eventual consistency on the dev server.** A write that references an object created moments earlier (campaign `template_id`, file upload `folder`) answers `400 Invalid pk ... does not exist` on the first attempt and succeeds 0.5-2.5 s later (on every one of more than 20 observations across the runs). The SDKs behave correctly (a 400 is never retried); callers who create-then-reference need their own short retry. One early Python run also failed on a template several minutes old, which was not explained. | server behaviour | all |
| L3 | **The API contract is wrong in three places**, and typed Java models silently drop the data: `templates/{id}/render` documents its response `data` as `TemplateRender` (the request body `{variables}`) while the server returns `subject` and `html_content` (Java returns an empty object); `POST /webhooks/` returns `secret`, `secret_masked`, `created_at`, `updated_at`, none declared (the Java record has no `secret`, so the signing secret cannot be read); `logout` returns an undeclared `message`. Python keeps the raw payload and TypeScript returns plain objects, so they still expose the data. Found by comparing the declared fields of 22 typed models with real responses. Needs a fix in the backend's contract, then regeneration. | contract defect | Java (data loss), Python/TypeScript (types wrong) |
| L4 | Python `tenants.list()`, `tenants.list_members()` and `auth.list_api_keys()` accept only `params=`, not `page` / `page_size`, so `iter_items(client.tenants.list)` raises `TypeError`. This contradicts the convention that every list method accepts them; TypeScript and Java do. | SDK defect | Python |
| L5 | `users.list` answers 403 for a tenant-admin account (probably platform-admin only); not an SDK defect. A failed login answers 400, not 401. | server behaviour | all |
| L6 | The mail provider's absence is invisible at send time (see Email above); `emails.send` answers `PROCESSING` and the failure appears only in the logs. | server behaviour | all |

### Resolution and retest

Changes made after the first live run (commits listed in section 15); the live run was then repeated with the final code.

| # | Resolution |
|---|---|
| L1 | **Fixed.** When no tenant is named (argument, per-call option, client default) the member calls and `tenants.get/update` ask the server which tenant the credentials resolve to (`GET auth/me/`, `current_tenant`) and use it; `current_tenant_id()` / `currentTenantId()` exposes it. `tenants.delete` is deliberately excluded: the id must always be explicit. Tests: unit tests per SDK (including the async layer), conformance C-23, and three injected defects (wrong field read, deletion that infers the id). The quick starts and README no longer pass a tenant id. |
| L2 | **Documented, not changed.** It is server behaviour; retrying a non-idempotent write inside the SDK would break the no-blind-retry rule. `docs/error-handling.md` tells callers to retry the second call themselves. |
| L3 | **Fixed in the SDKs, still open in the backend.** `openapi/sdk-overlay.yaml` adds `TemplateRenderResult` (and `templates.render` returns it), `secret`, `secret_masked`, `created_at`, `updated_at` on webhook creation, and `message` on logout, each with its evidence; the generators apply it on top of the unchanged snapshot. `tests/contract/test_overlay.py` fails once the backend contract declares these fields, so the overlay entries get deleted. The backend contract still needs the fix; this report cannot do that. After the change the live shape check finds **0 undeclared keys in 25 response models** (it was 3 of 22). |
| L4 | **Fixed.** `page` and `page_size` on `tenants.list`, `tenants.list_members`, `tenants.memberships.list`, `auth.list_api_keys`, `auth.api_keys.list`; unit tests and conformance C-23e check that `iter_items` walks them. |
| L5 | **Documented.** Role-limited endpoints (403) and the 400 on a failed login are server behaviour. |
| L6 | **Documented.** "Queued is not delivered"; configure a provider first. |

**Retest with the final code, same server and method.**

| SDK | PASS | PASS after retry | FAIL | Emails delivered |
|---|---|---|---|---|
| Python | 106 | 1 (L2) | 0 | 6 of 6 |
| TypeScript | 104 | 1 (L2) | 0 | 6 of 6 |
| Java | 103 | 2 (L2) | 0 | 6 of 6 |

The retest additionally asserts, in each SDK: `tenants.get()` and the member list work with only a URL and a key,
`current_tenant_id()` equals the tenant in the tenant list, `tenants.delete()` without an id is refused before any request,
render and webhook creation return typed fields (`subject`, `html_content`, `secret`), and `iter_items` /
`for await` walks the tenant and API-key lists. A server-side audit afterwards found 0 leftover test objects, no active
test API keys, and only the SES provider that was added on request.

Limits of the lookup (L1): it relies on the server's `current_tenant` for the credentials. It was exercised with an account
that has **one** tenant. For an account in several tenants the SDK takes whatever the server reports (documented as the
first active membership); that case is NOT VERIFIED.

Limits of this run: one server, one tenant, one tenant-admin account, one SES identity (ap-south-1); no platform-admin
operations; no load; webhook delivery was only triggered towards a reserved example domain and its result was not
inspected; SES behaviour outside this sender and region, including sandbox limits, is unknown.

## 13. Open questions needing a decision

None of these was changed, because the documentation does not decide them.

1. **Python `templates.create` sends defaults** (`status: "ACTIVE"`, empty strings) for omitted fields; TypeScript and Java
   send only what the caller supplied. If the server default differs, behaviour differs between SDKs.
2. **Id trimming**: the three languages probably disagree about which exotic whitespace characters are trimmed from ids (not tested).
3. **Iteration termination** when `next` is non-null but `page == total_pages`: all three SDKs stop at `total_pages` (a loop
   guard); the contract does not say.
4. **Retry-After: 0 or malformed** semantics beyond RFC 9110 (negative values, HTTP-date form): currently ignored in favour
   of the computed backoff in Python and TypeScript; not specified in the docs.
5. Backoff floor of 50 ms (all SDKs) is client policy, not documented.

## 14. Commands

```bash
scripts/verify_all.sh [workdir]            # everything in section 3, 9 and part of 8, from a clean copy
python tests/conformance/conformance.py    # cross-language suite
python tests/conformance/inject_defects.py --python-env <python with httpx, without nova_sdk>
scripts/mutation/run_python.sh | run_typescript.sh | run_java.sh
```

## 15. Commits

Branch `sdk-fixes-live-verified` (not pushed). Functional commits, oldest first: the live-run report; "expose the response fields the server really returns (overlay)"; "tenant-scoped calls work with only a server URL and an API key"; "tenant lookup, tenant paging and corrected response fields" (conformance); "a server URL and an API key are all you need; replace the placeholder host" (docs). Commit messages carry no co-author trailer.
No package was published, no registry upload, deployment, release or tag was made, and no workflow was triggered.
