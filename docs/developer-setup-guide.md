# Nova SDK: developer setup guide

Follow this guide to install a Nova SDK from Google Cloud Artifact Registry and send your first request. It takes about
10 minutes. Pick your language at step 4; steps 1 to 3 and 5 to 6 are the same for everyone.

The SDKs are **private**. They are not on PyPI, npmjs.com or Maven Central, so a plain `pip install`, `npm install` or
Maven build fails until you complete steps 1 to 3.

| Language | Package | Requires |
|---|---|---|
| Python | `infimatrix-nova-sdk` (import `nova_sdk`) | Python 3.10+ |
| Node.js / TypeScript | `@infimatrix/nova-sdk` | Node.js 18.17+ |
| Java | `com.infimatrix:nova-sdk` | JDK 17+ |

Current version: **0.2.1** (all three SDKs share one version).

## 1. Get access

Ask your team admin to grant your Google account (or your CI service account) the **Artifact Registry Reader**
role (`roles/artifactregistry.reader`) on the project, or on the specific repository:

- Project: `infimatrix-nova-artifacts`
- Console: <https://console.cloud.google.com/artifacts?project=infimatrix-nova-artifacts>

You need read access only. You never need write access to use the SDK.

Also ask for the three values you need to run the commands below:

| Placeholder | What it is | Where to find it |
|---|---|---|
| `<LOCATION>` | Registry location, e.g. `europe-west1` | Console > Artifact Registry > Repositories > *Location* column |
| `<REPOSITORY>` | Repository ID for your language | Same page > *Name* column (one repository per format: Python, npm, Maven) |
| `NOVA_BASE_URL` / `NOVA_API_KEY` | Your Nova server address and API key | See step 5 |

The project is always `infimatrix-nova-artifacts`. Set these once per terminal session and the commands below work as
written:

```bash
export AR_PROJECT=infimatrix-nova-artifacts
export AR_LOCATION=<LOCATION>                       # e.g. europe-west1
export AR_PYTHON_REPOSITORY=<python-repository-id>  # only the ones you need
export AR_NPM_REPOSITORY=<npm-repository-id>
export AR_MAVEN_REPOSITORY=<maven-repository-id>
```

## 2. Install the Google Cloud CLI

Install `gcloud` from <https://cloud.google.com/sdk/docs/install>, then check it:

```bash
gcloud --version
```

## 3. Sign in

```bash
gcloud auth login
gcloud config set project infimatrix-nova-artifacts
```

Check that you can see the repositories (you should get a list, not a permission error):

```bash
gcloud artifacts repositories list --project="$AR_PROJECT" --location="$AR_LOCATION"
```

`PERMISSION_DENIED` means step 1 is not finished. Ask your admin to confirm the role and the project.

## 4. Install the SDK

### Python

```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install keyring keyrings.google-artifactregistry-auth
pip install --index-url "https://${AR_LOCATION}-python.pkg.dev/${AR_PROJECT}/${AR_PYTHON_REPOSITORY}/simple/" \
  infimatrix-nova-sdk==0.2.1
```

The keyring plugin reuses your `gcloud` login, so no password is typed or stored.

To avoid repeating the URL, add it to `~/.config/pip/pip.conf` (Windows: `%APPDATA%\pip\pip.ini`) with the real values:

```ini
[global]
index-url = https://<LOCATION>-python.pkg.dev/infimatrix-nova-artifacts/<REPOSITORY>/simple/
```

Pin the SDK in `requirements.txt` and keep the registry URL on the first line:

```text
--index-url https://<LOCATION>-python.pkg.dev/infimatrix-nova-artifacts/<REPOSITORY>/simple/
infimatrix-nova-sdk==0.2.1
```

Note: if the repository holds only Nova packages, pip cannot find your other dependencies (`requests`, etc.) there. Ask
your admin for a *virtual* repository that combines this repository with PyPI. Avoid `--extra-index-url`: it allows
dependency-confusion attacks.

### Node.js / TypeScript

Create or edit `.npmrc` in your project root. It holds no secrets, so commit it:

```ini
@infimatrix:registry=https://<LOCATION>-npm.pkg.dev/infimatrix-nova-artifacts/<REPOSITORY>/
//<LOCATION>-npm.pkg.dev/infimatrix-nova-artifacts/<REPOSITORY>/:always-auth=true
```

(`gcloud artifacts print-settings npm --repository="$AR_NPM_REPOSITORY" --location="$AR_LOCATION" --scope=@infimatrix`
prints this for you.)

Only the `@infimatrix` scope uses Artifact Registry. Every other package still comes from npmjs.com.

Write a short-lived token to your user-level `~/.npmrc` (not the project), then install:

```bash
npx google-artifactregistry-auth
npm install @infimatrix/nova-sdk@0.2.1
```

The token expires after about an hour. If `npm install` later returns `401` or `403`, run
`npx google-artifactregistry-auth` again.

### Java (Maven)

1. Create `~/.m2/settings.xml` (never commit it) so Maven can authenticate:

   ```xml
   <settings>
     <servers>
       <server>
         <id>artifact-registry</id>
         <username>oauth2accesstoken</username>
         <password>${env.AR_ACCESS_TOKEN}</password>
       </server>
     </servers>
   </settings>
   ```

2. Export a token (valid 60 minutes) in the terminal that runs Maven:

   ```bash
   export AR_ACCESS_TOKEN="$(gcloud auth print-access-token)"
   ```

3. Add the repository and dependency to your `pom.xml`. The repository `<id>` must be `artifact-registry` to match
   `settings.xml`:

   ```xml
   <repositories>
     <repository>
       <id>artifact-registry</id>
       <url>https://<LOCATION>-maven.pkg.dev/infimatrix-nova-artifacts/<REPOSITORY></url>
     </repository>
   </repositories>

   <dependencies>
     <dependency>
       <groupId>com.infimatrix</groupId>
       <artifactId>nova-sdk</artifactId>
       <version>0.2.1</version>
     </dependency>
   </dependencies>
   ```

4. `mvn compile`. The first run downloads the SDK and `jackson-databind`.

**Gradle** (Kotlin DSL):

```kotlin
repositories {
    mavenCentral()
    maven {
        url = uri("https://<LOCATION>-maven.pkg.dev/infimatrix-nova-artifacts/<REPOSITORY>")
        credentials { username = "oauth2accesstoken"; password = System.getenv("AR_ACCESS_TOKEN") }
    }
}
dependencies { implementation("com.infimatrix:nova-sdk:0.2.1") }
```

## 5. Configure the SDK

The SDK needs your Nova server address and a credential. Get an API key from your Nova admin, or create one yourself
(see [getting started](getting-started.md#creating-credentials)). The key is shown **once**, so store it in a secret
manager.

```bash
export NOVA_BASE_URL=https://<your-nova-server>
export NOVA_API_KEY=nova_key_...
```

You do not need a workspace (tenant) ID. Set `NOVA_TENANT_ID` only if your account belongs to several workspaces and you
want a specific one.

Use the SDK from **server-side code only**. Never put the API key in a browser or mobile app
([why](authentication.md#never-ship-credentials-to-browsers)).

## 6. Send your first request

Each example reads `NOVA_BASE_URL` and `NOVA_API_KEY` from the environment and sends one email.

**Python**

```python
from nova_sdk import NovaClient

with NovaClient() as nova:
    email = nova.emails.send(
        recipient_email="ada@example.com", subject="Welcome!", html_content="<h1>Hi</h1>",
    )
    print(email.message_id, email.status)
```

Async: `from nova_sdk.aio import AsyncNovaClient`, then `async with AsyncNovaClient() as nova: await nova.health()`.

**TypeScript**

```ts
import { NovaClient } from "@infimatrix/nova-sdk";

const nova = new NovaClient();
const email = await nova.emails.send({
  recipient_email: "ada@example.com", subject: "Welcome!", html_content: "<h1>Hi</h1>",
});
console.log(email.message_id, email.status);
```

CommonJS also works: `const { NovaClient } = require("@infimatrix/nova-sdk");`.

**Java**

```java
import com.infimatrix.nova.NovaClient;
import com.infimatrix.nova.models.SendEmailRequest;

NovaClient nova = NovaClient.builder().build();
var email = nova.emails().send(SendEmailRequest.builder()
        .recipientEmail("ada@example.com").subject("Welcome!").htmlContent("<h1>Hi</h1>").build());
System.out.println(email.messageId() + " " + email.status());
```

If this prints a message ID and a status, you are done. To check connectivity without sending anything, call the health
endpoint: `nova.health()` (same name in all three SDKs).

## 7. Use it in CI

Do not use a person's login in CI. Use a **service account** with the Artifact Registry Reader role, and short-lived
tokens:

- On GitHub Actions or another OIDC-capable CI, prefer Workload Identity Federation with
  [`google-github-actions/auth`](https://github.com/google-github-actions/auth) (no stored keys).
- Then get a token with `gcloud auth print-access-token` and pass it per tool:

| Tool | CI command |
|---|---|
| pip | `pip install --index-url "https://oauth2accesstoken:$(gcloud auth print-access-token)@<LOCATION>-python.pkg.dev/infimatrix-nova-artifacts/<REPOSITORY>/simple/" infimatrix-nova-sdk==0.2.1` |
| npm | `export NPM_CONFIG_USERCONFIG="$RUNNER_TEMP/npmrc"; echo "//<LOCATION>-npm.pkg.dev/infimatrix-nova-artifacts/<REPOSITORY>/:_authToken=$(gcloud auth print-access-token)" > "$NPM_CONFIG_USERCONFIG"; npm ci` |
| Maven / Gradle | `export AR_ACCESS_TOKEN="$(gcloud auth print-access-token)"` then `mvn verify` / `gradle build` |

Never commit tokens, and never print them in build logs.

## Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| `PERMISSION_DENIED` / `403` on install | Missing `roles/artifactregistry.reader`. Ask your admin. Check you are signed in as the right account: `gcloud auth list`. |
| `401 Unauthorized` (npm, Maven) | Token expired (1 hour). Re-run `npx google-artifactregistry-auth` or re-export `AR_ACCESS_TOKEN`. |
| pip: `No matching distribution found for infimatrix-nova-sdk` | Wrong `<LOCATION>`/`<REPOSITORY>` in the URL, URL missing the trailing `/simple/`, or keyring plugin not installed. |
| pip: other packages (e.g. `httpx`) not found | The index only holds Nova packages. Use a virtual repository that includes PyPI (see step 4). |
| npm: `E404 @infimatrix/nova-sdk` | `.npmrc` scope line missing or wrong, or the version does not exist. List versions: `gcloud artifacts versions list --package=nova-sdk --repository="$AR_NPM_REPOSITORY" --location="$AR_LOCATION"`. |
| Maven: `Could not transfer artifact ... 401` | `<id>` in `pom.xml` does not match `<id>` in `settings.xml`, or `AR_ACCESS_TOKEN` is not exported in that shell. |
| `NovaAuthenticationError` / `401` from Nova | `NOVA_API_KEY` is wrong, revoked or expired. This is the Nova API, not the registry. |
| Connection error to Nova | Check `NOVA_BASE_URL` (include `https://`; a trailing `/api/v1` is accepted). |

Handle errors in your code with the typed exceptions described in [error handling](error-handling.md).

## Next steps

- [Authentication and tenancy](authentication.md)
- [Error handling](error-handling.md) and [conventions](conventions.md) (pagination, retries, uploads)
- Per-language reference: [Python](../sdks/python/README.md), [TypeScript](../sdks/typescript/README.md),
  [Java](../sdks/java/README.md)
- [Versioning and compatibility](versioning.md): how to choose and upgrade versions
