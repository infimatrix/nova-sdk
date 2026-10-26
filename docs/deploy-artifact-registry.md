# Deploying the SDKs to Google Cloud Artifact Registry

Step-by-step guide to publish the Nova SDKs to [Artifact Registry](https://docs.cloud.google.com/artifact-registry/docs)
(AR). Background and safeguards: [distribution](distribution.md) and [releasing](releasing.md). Consumers: see
[Python](using-python.md), [Node.js](using-node.md) and [Java](using-java.md).

| SDK | AR format | Publishing |
|---|---|---|
| Python | [Python](https://docs.cloud.google.com/artifact-registry/docs/python) | GitHub Actions on `python-v*` tags, or manual `twine` |
| TypeScript | [npm](https://docs.cloud.google.com/artifact-registry/docs/nodejs) | GitHub Actions on `typescript-v*` tags, or manual `npm publish` |
| Java | [Maven](https://docs.cloud.google.com/artifact-registry/docs/java) | **Manual `mvn deploy` only** (no workflow, no `distributionManagement` yet, see [below](#3-java-maven)) |

Replace `<PROJECT>`, `<LOCATION>` (e.g. `europe-west1`) and the repository names with your own. Nothing in this
repository is created for you.

## 1. One-time Google Cloud setup

```bash
gcloud config set project <PROJECT>
gcloud services enable artifactregistry.googleapis.com iamcredentials.googleapis.com

for fmt in python npm maven; do
  gcloud artifacts repositories create nova-$fmt \
    --repository-format=$fmt --location=<LOCATION> \
    --description="Nova SDK ($fmt)"
done
# Maven only: keep release versions immutable
gcloud artifacts repositories update nova-maven --location=<LOCATION> --version-policy=release
```

Publisher identity (CI) and readers (consumers), least privilege, per repository:

```bash
gcloud iam service-accounts create nova-sdk-publisher

for repo in nova-python nova-npm nova-maven; do
  gcloud artifacts repositories add-iam-policy-binding $repo --location=<LOCATION> \
    --member="serviceAccount:nova-sdk-publisher@<PROJECT>.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.writer"
  gcloud artifacts repositories add-iam-policy-binding $repo --location=<LOCATION> \
    --member="group:<CONSUMERS_GROUP>" --role="roles/artifactregistry.reader"
done
```

Verify: `gcloud artifacts repositories list --location=<LOCATION>`.

## 2. Python and TypeScript: GitHub Actions release

The workflows [release-python.yml](../.github/workflows/release-python.yml) and
[release-typescript.yml](../.github/workflows/release-typescript.yml) build, verify and publish with short-lived
credentials from Workload Identity Federation (WIF). No key is stored.

**a. Workload Identity Federation** (restrict it to this repository):

```bash
gcloud iam workload-identity-pools create github --location=global
gcloud iam workload-identity-pools providers create-oidc github-oidc \
  --location=global --workload-identity-pool=github \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --attribute-condition="assertion.repository=='infimatrix/nova-sdk'"

gcloud iam service-accounts add-iam-policy-binding \
  nova-sdk-publisher@<PROJECT>.iam.gserviceaccount.com \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github/attribute.repository/infimatrix/nova-sdk"
```

**b. GitHub environment** `artifact-registry` (Settings → Environments): add **Required reviewers** and limit
deployment tags to `python-v*` and `typescript-v*`. Add these **variables** (not secrets):

| Variable | Value |
|---|---|
| `GCP_PROJECT_ID` | `<PROJECT>` |
| `AR_LOCATION` | `<LOCATION>` |
| `AR_PYTHON_REPOSITORY` | `nova-python` |
| `AR_NPM_REPOSITORY` | `nova-npm` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/<PROJECT_NUMBER>/locations/global/workloadIdentityPools/github/providers/github-oidc` |
| `GCP_SERVICE_ACCOUNT` | `nova-sdk-publisher@<PROJECT>.iam.gserviceaccount.com` |

**c. Release**

1. Bump the version (`sdks/python/src/nova_sdk/_version.py`; or `sdks/typescript/package.json` **and**
   `src/version.ts`) and the SDK `CHANGELOG.md`; merge to `main`.
2. `git tag python-v0.2.0 && git push origin python-v0.2.0` (or `typescript-v0.1.0`). The tag must equal the package
   version or the build job fails.
3. Approve the `artifact-registry` environment when the workflow pauses.

Rehearse without publishing: Actions → *Run workflow* with `publish` unchecked.

**d. Verify**

```bash
gcloud artifacts packages list --repository=nova-python --location=<LOCATION>
gcloud artifacts versions list --package=infimatrix-nova-sdk --repository=nova-python --location=<LOCATION>
gcloud artifacts packages list --repository=nova-npm --location=<LOCATION>
```

### Manual publish (fallback, from a trusted workstation)

```bash
gcloud auth login   # an identity with Artifact Registry Writer

# Python
cd sdks/python && python -m build && twine check dist/*
pip install keyring keyrings.google-artifactregistry-auth
twine upload --repository-url https://<LOCATION>-python.pkg.dev/<PROJECT>/nova-python/ dist/*

# npm: .npmrc must map @infimatrix to the AR repo (see using-node.md); the prepublish guard enforces it
cd sdks/typescript && npm ci && npm run build && npx google-artifactregistry-auth && npm publish
```

## 3. Java (Maven)

The Java SDK has no release workflow and its [pom.xml](../sdks/java/pom.xml) has no `distributionManagement`, so
nothing can be deployed accidentally. To publish a release manually:

1. Add the target to your **own** `~/.m2/settings.xml` (or pass it on the command line); do not commit credentials:

   ```xml
   <settings>
     <servers>
       <server>
         <id>artifact-registry</id>
         <username>oauth2accesstoken</username>
         <!-- short-lived token, e.g. generated into this file by a script: gcloud auth print-access-token -->
         <password>${env.AR_ACCESS_TOKEN}</password>
       </server>
     </servers>
   </settings>
   ```

2. Run the full verification, then deploy to the repository (`-DaltDeploymentRepository` avoids editing the pom):

   ```bash
   export AR_ACCESS_TOKEN="$(gcloud auth print-access-token)"
   cd sdks/java
   mvn -B verify
   mvn -B deploy -DskipTests \
     -DaltDeploymentRepository=artifact-registry::https://<LOCATION>-maven.pkg.dev/<PROJECT>/nova-maven
   ```

   Alternative: `gcloud artifacts print-settings mvn --repository=nova-maven --location=<LOCATION>` prints a ready-made
   `pom.xml`/`settings.xml` using the `artifactregistry-maven-wagon` extension (credentials from `gcloud`/ADC).
3. Verify: `gcloud artifacts versions list --package=com.infimatrix:nova-sdk --repository=nova-maven --location=<LOCATION>`.

Release repositories with `--version-policy=release` reject re-uploading an existing version; bump `<version>` in
`pom.xml` and `CHANGELOG.md` first. Adding a tag-triggered `release-java.yml` that mirrors the other two (WIF, approval
environment, `AR_MAVEN_REPOSITORY` variable) is future work.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `403 Permission denied` on upload | the identity lacks `roles/artifactregistry.writer` **on that repository** |
| `401` on install | expired token (60 min) or missing `Artifact Registry Reader` |
| Workflow stops at `Require registry configuration` | an environment variable above is unset |
| WIF `unauthorized_client` | attribute condition does not match the repository, or the service-account binding is missing |
| `Tag … != package version …` | bump the version file before tagging |
| `npm publish` refused by guard | `@infimatrix:registry` does not point to a `*-npm.pkg.dev` host |
| Maven `409`/"already exists" | release versions are immutable; publish a new version |
