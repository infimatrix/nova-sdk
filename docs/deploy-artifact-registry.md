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

## 2. Python and TypeScript

This repository has a single CI workflow ([ci.yml](../.github/workflows/ci.yml): gitleaks, CodeQL and tests). It has no
release or publish step and holds no cloud credentials, so publishing is done by a person from a trusted workstation.

**Publish from a trusted workstation**

Bump the version (`sdks/python/src/nova_sdk/_version.py`; or `sdks/typescript/package.json` **and** `src/version.ts`) and the
SDK `CHANGELOG.md`, merge to `main`, then:

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

No SDK has a release workflow, and the Java [pom.xml](../sdks/java/pom.xml) has no `distributionManagement`, so
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
