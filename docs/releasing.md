# Releasing

Packages are published **only** to Google Cloud Artifact Registry (see [distribution](distribution.md)). Ordinary CI
(`contract.yml`, `sdk-python.yml`, `sdk-typescript.yml`) never needs Google Cloud credentials and never publishes.
Merging code publishes nothing.

> **Scope:** release workflows exist for Python and TypeScript only. The Java SDK (`sdks/java`) is built and tested in CI
> (`sdk-java.yml`, which runs `mvn verify` and never `deploy`), but it has no release workflow and no `distributionManagement`.
> A Maven release to Artifact Registry is a separate, future task.

## One-time setup (Google Cloud administrator)

Nothing here has been created by this repository; use your own names. Commands are illustrative.

1. **Repositories** (in the chosen project and location):
   ```bash
   gcloud artifacts repositories create <PY_REPO>  --repository-format=python --location=<LOCATION> --project=<PROJECT>
   gcloud artifacts repositories create <NPM_REPO> --repository-format=npm    --location=<LOCATION> --project=<PROJECT>
   ```
   Consider enabling cleanup policies and, for the npm repository, a virtual repository that also fronts public npm.
2. **Publisher service account** with the **Artifact Registry Writer** role (`roles/artifactregistry.writer`) granted on
   those two repositories only (not project-wide). Consumers get **Artifact Registry Reader** (`roles/artifactregistry.reader`).
3. **Workload Identity Federation** — a pool and a GitHub OIDC provider whose *attribute condition* restricts tokens to
   this repository, e.g. `assertion.repository == 'infimatrix/nova-sdk'` (and ideally the `artifact-registry`
   environment), then allow that principal to impersonate the publisher service account
   (`roles/iam.workloadIdentityUser`). Guide: <https://github.com/google-github-actions/auth>.
4. **GitHub** (Settings of `infimatrix/nova-sdk`):
   - Environment **`artifact-registry`** with **Required reviewers** (and "prevent self-review" if possible),
     restricted to tags matching `python-v*` and `typescript-v*`.
   - Environment **variables** (not secrets): `GCP_PROJECT_ID`, `AR_LOCATION`, `AR_PYTHON_REPOSITORY`, `AR_NPM_REPOSITORY`,
     `GCP_WORKLOAD_IDENTITY_PROVIDER`, `GCP_SERVICE_ACCOUNT`.
   - A tag ruleset protecting `python-v*` / `typescript-v*` so only maintainers can create them.

## Releasing an SDK

1. Update the version (`sdks/python/src/nova_sdk/_version.py`, or `sdks/typescript/package.json` **and**
   `src/version.ts`) and the SDK's `CHANGELOG.md`.
2. Merge to `main`; CI must be green.
3. Tag and push: `git tag python-v0.2.0 && git push origin python-v0.2.0` (or `typescript-v0.1.0`).
4. The release workflow builds and verifies without any cloud access, then pauses at the `artifact-registry`
   environment. A reviewer approves; only then does the `publish` job obtain a short-lived Google credential through
   Workload Identity Federation and upload to Artifact Registry.

Rehearse without publishing: run the workflow manually (Actions → Run workflow) on a branch or tag with `publish`
unchecked; it only builds and verifies. A manual run publishes only when it is on a `*-v*` tag **and** `publish` is checked,
and it still needs the environment approval.

## Safeguards

| Safeguard | Where |
|---|---|
| Publish job only for `python-v*` / `typescript-v*` tags in `infimatrix/nova-sdk` | `if:` of the `publish` jobs |
| Human approval | `environment: artifact-registry` required reviewers (GitHub setting — verify it is configured) |
| Short-lived credentials, no stored keys | Workload Identity Federation, 60-minute access token |
| Least privilege | Writer role on the two repositories only; `id-token: write` only in `publish` |
| Destination cannot be changed by input | registry URL built from environment variables; no PyPI/npm/Maven destinations |
| Wrong-registry protection | `Private :: Do Not Upload` classifier; `require-artifact-registry.mjs` guard |
| Tag/version agreement, lint, tests, audit before publish | `build` job |
| Tokens never in the repo | `.npmrc` is created in `$RUNNER_TEMP` and removed; token is masked |

If the environment has no required reviewers, a tag push would proceed to publish (credentials permitting). Treat the
environment configuration as part of the release process and verify it before the first tag.

## Local verification (no cloud, no publishing)

```bash
cd sdks/python && python -m build && twine check dist/*
cd sdks/typescript && npm ci && npm run typecheck && npm test && npm run build && npm run check:package
```
