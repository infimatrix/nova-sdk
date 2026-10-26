# Distribution: Google Cloud Artifact Registry

Nova SDKs are distributed **only** through Google Cloud Artifact Registry (AR). They are not published to PyPI, the
public npm registry, Maven Central or any other public index. The GitHub repository is public; the packages are not.

| SDK | AR format | Repository URL | Status |
|---|---|---|---|
| Python `infimatrix-nova-sdk` | Python | `https://<LOCATION>-python.pkg.dev/<PROJECT>/<REPOSITORY>/` (install via `…/simple/`) | Release workflow ready |
| TypeScript `@infimatrix/nova-sdk` | npm | `https://<LOCATION>-npm.pkg.dev/<PROJECT>/<REPOSITORY>/` | Release workflow ready |
| Java `com.infimatrix:nova-sdk` | Maven | `https://<LOCATION>-maven.pkg.dev/<PROJECT>/<REPOSITORY>` | SDK implemented; **no release workflow or `distributionManagement` yet** |
| Kotlin/Android | Maven | same format | SDK not implemented |
| Go | Go | `https://<LOCATION>-go.pkg.dev/<PROJECT>/<REPOSITORY>` | SDK not implemented |

Supported formats: <https://docs.cloud.google.com/artifact-registry/docs/supported-formats>.
Java is built and tested locally only: its `pom.xml` has no `distributionManagement`, `mvn deploy` is not configured, and no
release workflow exists. Publishing it to Artifact Registry Maven (and the Kotlin and Go rows) is future work.

## Nothing is hard-coded

Project, location, repository names and the CI identity are configuration, never source code. The release workflows read
them from variables of the `artifact-registry` GitHub environment:

| Variable | Meaning |
|---|---|
| `GCP_PROJECT_ID` | Google Cloud project that owns the repositories |
| `AR_LOCATION` | Repository location, e.g. a region |
| `AR_PYTHON_REPOSITORY` | ID of the Python repository |
| `AR_NPM_REPOSITORY` | ID of the npm repository |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Full resource name of the Workload Identity provider |
| `GCP_SERVICE_ACCOUNT` | Service account the workflow impersonates |

These are identifiers, not secrets, so they are variables. No key, token or password is stored in the repository or in
GitHub secrets.

## Installing (consumers)

Consumers need read access (`Artifact Registry Reader`) on the repository and a credential.

**Python** — see <https://docs.cloud.google.com/artifact-registry/docs/python/authentication>:

```bash
# local development: keyring backend uses your gcloud / ADC credentials
pip install keyring keyrings.google-artifactregistry-auth
pip install --index-url https://<LOCATION>-python.pkg.dev/<PROJECT>/<REPOSITORY>/simple/ infimatrix-nova-sdk

# CI: short-lived access token (valid 60 minutes)
pip install --index-url "https://oauth2accesstoken:$(gcloud auth print-access-token)@<LOCATION>-python.pkg.dev/<PROJECT>/<REPOSITORY>/simple/" infimatrix-nova-sdk
```

Prefer `--index-url` for this repository plus a trusted mirror/remote repository for other dependencies, or
`--extra-index-url` only after reading the dependency-confusion note in the AR documentation.

**npm** — see <https://docs.cloud.google.com/artifact-registry/docs/nodejs/authentication>. Map the scope to the
repository in the project's `.npmrc` (no credentials in this file):

```ini
@infimatrix:registry=https://<LOCATION>-npm.pkg.dev/<PROJECT>/<REPOSITORY>/
//<LOCATION>-npm.pkg.dev/<PROJECT>/<REPOSITORY>/:always-auth=true
```

Put the token in your per-user npm config (`~/.npmrc`) or use `npx google-artifactregistry-auth` to refresh it.
Because the scope is mapped, all other packages still come from your default registry.

## Safeguards against publishing elsewhere

- Python: the package carries the `Private :: Do Not Upload` classifier, which the public PyPI rejects.
- npm: `prepublishOnly` runs `sdks/typescript/scripts/require-artifact-registry.mjs`, which fails unless the effective
  `@infimatrix:registry` is an HTTPS `*-npm.pkg.dev` host. The release workflow runs the same guard before `npm publish`.
- Release workflows contain no PyPI, npm or Maven destination; `tests/contract/test_release_safeguards.py` enforces this.
