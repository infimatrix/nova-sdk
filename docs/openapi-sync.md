# Updating the OpenAPI contract

The Nova backend owns the API. This repository keeps a committed snapshot,
`openapi/nova-api.yaml`, so SDK builds and CI are reproducible and need no backend.

## Obtaining the artifact

The backend generates it with drf-spectacular (in the backend repository: `scripts/gen-openapi.sh`, which writes
`openapi/nova-api.yaml`). Publish or hand over that file for each backend release; the document's `info.version`
identifies the API version. Any of these is a valid `SOURCE`:

- a local copy of the backend's `openapi/nova-api.yaml`,
- a release asset or build artifact URL (`https://…`; plain `http://` is refused),
- JSON from the running API's schema endpoint (`/api/v1/schema/?format=json`).

## Workflow

```bash
pip install -r requirements-dev.txt

python scripts/sync_openapi.py SOURCE --dry-run   # validate and list added (+), removed (-), changed (~) operations
python scripts/sync_openapi.py SOURCE             # write openapi/nova-api.yaml

python scripts/gen_python_models.py
python scripts/gen_python_async.py                # needs ruff (see requirements-dev.txt)
python scripts/gen_ts_types.py
python scripts/gen_java_models.py
python scripts/check_sdk_coverage.py --strict
pytest
```

If `check_sdk_coverage.py` reports a missing operation, implement it in **both** SDKs (or add a justified entry to
`openapi/sdk-exclusions.yaml`), then bump the SDK versions and changelogs as described in [versioning](versioning.md).

## Drift detection

`python scripts/sync_openapi.py SOURCE --check` exits 1 when the snapshot differs from `SOURCE`, listing the operation
differences. Run it from a scheduled job or from the backend's release pipeline against the newest artifact.

## What is validated

`sync_openapi.py` refuses to write unless SOURCE parses, declares `openapi: 3.x` and passes `openapi-spec-validator`.
`pytest` then enforces the Nova conventions (envelope, auth, tenant header, pagination parameters, error envelope).
