# Releasing

Packages are published **only** to Google Cloud Artifact Registry (see [distribution](distribution.md)). The repository's
single CI workflow ([ci.yml](../.github/workflows/ci.yml): gitleaks, CodeQL and tests) never needs Google Cloud
credentials and never publishes. Merging code publishes nothing, and there are no release workflows: a release is a
manual step by someone with Artifact Registry Writer access.

## Releasing an SDK

1. Update the version (`sdks/python/src/nova_sdk/_version.py`, or `sdks/typescript/package.json` **and**
   `src/version.ts`; Java: `sdks/java/pom.xml`) and the SDK's `CHANGELOG.md`.
2. Merge to `main`; CI must be green.
3. Publish from a trusted workstation as described in [deploy-artifact-registry](deploy-artifact-registry.md)
   (Python and TypeScript: section 2; Java: section 3).

## Safeguards

| Safeguard | Where |
|---|---|
| CI cannot publish or authenticate to a cloud | no secrets, no `id-token`, no publish commands in `ci.yml`; enforced by `tests/contract/test_release_safeguards.py` |
| Wrong-registry protection | `Private :: Do Not Upload` classifier; `require-artifact-registry.mjs` guard in `prepublishOnly` |
| Least privilege | Writer role on the target repositories only; consumers get Reader |

## Local verification (no cloud, no publishing)

```bash
cd sdks/python && python -m build && twine check dist/*
cd sdks/typescript && npm ci && npm run typecheck && npm test && npm run build && npm run check:package
cd sdks/java && mvn -B verify
```
