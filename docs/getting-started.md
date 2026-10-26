# Getting started

Every SDK needs three things: the API **base URL**, a **credential** (API key or JWT) and, for tenant-scoped
endpoints, a **tenant ID**. All of them can come from environment variables:

| Variable | Meaning |
|---|---|
| `NOVA_BASE_URL` | API origin, e.g. `https://api.example.com` (a trailing `/api/v1` is accepted) |
| `NOVA_API_KEY` | API key (`nova_key_…`), created via `POST /api/v1/auth/api-keys/` |
| `NOVA_ACCESS_TOKEN` | JWT from `POST /api/v1/auth/login/` |
| `NOVA_TENANT_ID` | Default tenant UUID sent as `X-Tenant-ID` |

## Python

SDKs are served from a private Google Cloud Artifact Registry repository, not PyPI; see [distribution](distribution.md) for
authentication.

```bash
pip install --index-url https://<LOCATION>-python.pkg.dev/<PROJECT>/<REPOSITORY>/simple/ infimatrix-nova-sdk
```

```python
from nova_sdk import NovaClient

with NovaClient() as nova:                       # reads NOVA_* variables
    email = nova.emails.send(recipient_email="ada@example.com", subject="Welcome!", html_content="<h1>Hi</h1>")
    print(email.message_id, email.status)
```

Async: `from nova_sdk.aio import AsyncNovaClient`. See [sdks/python/README.md](../sdks/python/README.md).

## Java

Build the SDK locally (it is not published yet) and depend on `com.infimatrix:nova-sdk`:

```bash
cd sdks/java && mvn install      # local ~/.m2 only
```

```java
NovaClient nova = NovaClient.builder().build();   // reads NOVA_* variables
var email = nova.emails().send(SendEmailRequest.builder()
        .recipientEmail("ada@example.com").subject("Welcome!").htmlContent("<h1>Hi</h1>").build());
```

See [sdks/java/README.md](../sdks/java/README.md).

## TypeScript / Node.js

Map the `@infimatrix` scope to the Artifact Registry npm repository first (see [distribution](distribution.md)):

```bash
npm install @infimatrix/nova-sdk
```

```ts
import { NovaClient } from "@infimatrix/nova-sdk";

const nova = new NovaClient();                   // reads NOVA_* variables
const email = await nova.emails.send({ recipient_email: "ada@example.com", subject: "Welcome!", html_content: "<h1>Hi</h1>" });
```

See [sdks/typescript/README.md](../sdks/typescript/README.md). Browsers are not supported; see
[authentication](authentication.md#never-ship-credentials-to-browsers).

## Creating credentials

1. `POST /api/v1/auth/register/` (or use an existing account) then `POST /api/v1/auth/login/`.
2. `POST /api/v1/auth/api-keys/` with the access token. The raw key is shown **once**; store it in a secret manager.
3. Use the key from your server with the SDK of your choice.
