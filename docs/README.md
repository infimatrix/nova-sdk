# Nova SDKs

Nova's REST API is the source of truth. SDKs are thin, idiomatic clients that stay aligned with it
through a committed, machine-readable contract.

```text
Nova backend (Django REST + drf-spectacular)
        │  publishes nova-api.yaml (versioned artifact)
        ▼
scripts/sync_openapi.py ──▶ openapi/nova-api.yaml  (committed snapshot, this repo)
                                   │
          ┌────────────────────────┼─────────────────────────┐
          ▼                        ▼                         ▼
 gen_python_models.py      gen_ts_types.py        gen_java_models.py     check_sdk_coverage.py
 gen_python_async.py              │                      │                       │
          ▼                       ▼                      ▼                       ▼
   sdks/python               sdks/typescript         sdks/java      (hand-written transport, auth, retries,
                                                                    errors and resources in every SDK)
```

## Guides

- [Getting started](getting-started.md)
- [Authentication and tenancy](authentication.md)
- [Error handling](error-handling.md)
- [Conventions every SDK follows](conventions.md)
- [Versioning and compatibility matrix](versioning.md)
- Using the SDKs: [Python](using-python.md), [Node.js](using-node.md), [Java](using-java.md)
- [Deploying to Artifact Registry (step by step)](deploy-artifact-registry.md)
- [Distribution via Google Cloud Artifact Registry](distribution.md)
- [Releasing](releasing.md)
- [Verification plan](verification-plan.md) and [verification report](verification-report.md)
- [Updating the OpenAPI contract](openapi-sync.md)
- [Adding a new language](adding-a-language.md)

## The contract

- File: [openapi/nova-api.yaml](../openapi/nova-api.yaml) (OpenAPI 3.0.3), a **committed snapshot** of the
  document the Nova backend generates. This repository does not contain or run the backend; update the snapshot
  with `scripts/sync_openapi.py` ([guide](openapi-sync.md)).
- Documents the **real wire format**: the `{success, message, data, errors, meta}` envelope, the
  `{success, pagination, results}` page shape inside `data`, the shared error envelope, multipart uploads,
  CSV exports, and the `X-Tenant-ID` header.
- [openapi/sdk-exclusions.yaml](../openapi/sdk-exclusions.yaml) lists the few operations SDKs intentionally
  do not expose, each with a reason.
- Known deviations that SDKs tolerate: a few endpoints return legacy, non-enveloped error bodies such as
  `{"error": "…"}` or `{"detail": "…"}`; the health endpoint's 503 body is not enveloped.

## Keeping everything aligned

| Check | Where | Fails when |
|---|---|---|
| `pytest` (`tests/contract/`) | `contract.yml` | the snapshot is invalid OpenAPI, or violates envelope/auth/tenant/pagination rules |
| `scripts/sync_openapi.py SOURCE --check` | manual / backend-triggered | the snapshot differs from the backend's current artifact |
| `scripts/check_sdk_coverage.py --strict` | `contract.yml`, SDK workflows | an SDK is missing a contract operation or calls one that does not exist |
| `scripts/gen_python_models.py --check`, `gen_python_async.py --check`, `gen_ts_types.py --check`, `gen_java_models.py --check` | `contract.yml`, SDK workflows | generated code is stale |

Checks that need a running backend (every route documented, real responses validated against the schemas) live in the
backend repository's `tests/contract/`.
