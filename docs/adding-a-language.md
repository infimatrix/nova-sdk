# Adding a new language SDK

Use this process for Kotlin/Android, Go or anything else (`sdks/java` is a worked example: generator
`scripts/gen_java_models.py`, coverage scanner entry in `scripts/check_sdk_coverage.py`, CI in `sdk-java.yml`). A language is "supported" only when every step
below is done; until then it must not appear as supported in READMEs or package metadata.

1. **Start from the contract.** Read [conventions](conventions.md). Never hand-write request/response shapes that
   the OpenAPI document already defines.
2. **Create `sdks/<language>/`** with its own build file, tests, README, LICENSE and CHANGELOG. Do not place
   code for one language inside another's package.
3. **Models.** Generate them from `openapi/nova-api.yaml`. Either extend the existing generators
   (`scripts/gen_python_models.py`, `scripts/gen_ts_types.py` are ~150 lines each) or pin an OpenAPI generator
   version and document the exact command. Generated files carry an "AUTO-GENERATED" banner and a `--check` mode so CI can
   verify reproducibility. Android/Kotlin deserves a dedicated decision (coroutines, minSdk, OkHttp/Ktor, R8
   rules); do not claim Android support just because a Java artifact runs there.
4. **Hand-write the transport** (it carries the behaviour that generators get wrong): auth headers, tenant header,
   correlation ID, timeouts, retry rules for idempotent calls only, `Retry-After`, no redirect following,
   envelope unwrapping, error mapping, secret redaction, multipart upload, CSV/204 handling.
5. **Resources.** One class per API area with the verb names from the conventions. Keep each call's literal
   `"METHOD", "path"` pair greppable, or extend the scanner in `scripts/check_sdk_coverage.py` for the language
   (see `SDKS`, `CALL_RE`, `LIST_RE`) so `check_sdk_coverage.py --strict` measures it.
6. **Tests.** Mocked-HTTP unit tests for every resource, retry/timeout/redirect/error mapping tests, a test against
   a real local HTTP server, and a packaging test that installs the built artifact in a clean project.
7. **CI.** Add `.github/workflows/sdk-<language>.yml` (lint/test matrix over supported runtimes, generated-code
   reproducibility, strict coverage, artifact verification, dependency audit) and a gated
   `release-<language>.yml` that publishes only to the matching Artifact Registry format (Maven for Java/Kotlin,
   Go for Go; see [distribution](distribution.md)) through the `artifact-registry` environment and Workload Identity Federation.
8. **Docs.** Add the language to the tables in [README.md](README.md), [versioning.md](versioning.md) and the
   root README, and document runtime support and known differences.
9. **Review checklist:** `check_sdk_coverage.py --strict` is 100%, the compatibility matrix is updated,
   no secrets in logs or error messages, no runtime dependencies without justification.
