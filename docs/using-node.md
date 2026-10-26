# Using the Node.js / TypeScript SDK

Package `@infimatrix/nova-sdk`, Node.js 18.17+, ESM and CommonJS, no runtime dependencies. Served only from Artifact
Registry ([deploy guide](deploy-artifact-registry.md)). Reference: [sdks/typescript/README.md](../sdks/typescript/README.md).
Server-side only: never ship API keys to browsers ([why](authentication.md#never-ship-credentials-to-browsers)).

## 1. Point the scope at Artifact Registry

Project `.npmrc` (safe to commit, no credentials). See the
[Node.js authentication docs](https://docs.cloud.google.com/artifact-registry/docs/nodejs/authentication).

```ini
@infimatrix:registry=https://<LOCATION>-npm.pkg.dev/<PROJECT>/<REPOSITORY>/
//<LOCATION>-npm.pkg.dev/<PROJECT>/<REPOSITORY>/:always-auth=true
```

Only the `@infimatrix` scope uses AR; every other package still comes from your default registry.
`gcloud artifacts print-settings npm --repository=<REPOSITORY> --location=<LOCATION> --scope=@infimatrix` prints the same.

## 2. Authenticate

Needs `roles/artifactregistry.reader`.

```bash
gcloud auth login
npx google-artifactregistry-auth      # writes a short-lived token to ~/.npmrc; re-run when it expires
```

**CI**: write the token to a per-job npm config, never into the repository:

```bash
export NPM_CONFIG_USERCONFIG="$RUNNER_TEMP/npmrc"; umask 077
echo "//<LOCATION>-npm.pkg.dev/<PROJECT>/<REPOSITORY>/:_authToken=$(gcloud auth print-access-token)" > "$NPM_CONFIG_USERCONFIG"
npm ci
```

## 3. Install and use

```bash
npm install @infimatrix/nova-sdk
```

```ts
import { NovaClient } from "@infimatrix/nova-sdk";

const nova = new NovaClient();                   // reads NOVA_BASE_URL, NOVA_API_KEY, NOVA_TENANT_ID
const email = await nova.emails.send({
  recipient_email: "ada@example.com", subject: "Welcome!", html_content: "<h1>Hi</h1>",
});
console.log(email.message_id, email.status);
```

CommonJS: `const { NovaClient } = require("@infimatrix/nova-sdk");`. Types ship with the package. See
[error handling](error-handling.md) and [conventions](conventions.md).
