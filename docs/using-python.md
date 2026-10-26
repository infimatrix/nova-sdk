# Using the Python SDK

Package `infimatrix-nova-sdk`, Python 3.10+, import name `nova_sdk`. Served only from Artifact Registry
([deploy guide](deploy-artifact-registry.md)). Full reference: [sdks/python/README.md](../sdks/python/README.md).

## 1. Authenticate to Artifact Registry

Needs `roles/artifactregistry.reader` on the repository. See the
[Python authentication docs](https://docs.cloud.google.com/artifact-registry/docs/python/authentication).

```bash
gcloud auth login                       # or Application Default Credentials / a service account
pip install keyring keyrings.google-artifactregistry-auth
```

## 2. Install

```bash
pip install --index-url https://<LOCATION>-python.pkg.dev/<PROJECT>/<REPOSITORY>/simple/ infimatrix-nova-sdk
```

Make it permanent in `pip.conf` (`~/.config/pip/pip.conf`) or per project:

```ini
[global]
index-url = https://<LOCATION>-python.pkg.dev/<PROJECT>/<REPOSITORY>/simple/
```

`requirements.txt` pinned to the repository: first line `--index-url https://<LOCATION>-python.pkg.dev/<PROJECT>/<REPOSITORY>/simple/`,
then `infimatrix-nova-sdk==0.1.0`. Use a remote/virtual AR repository in front of PyPI for your other dependencies rather
than `--extra-index-url` (dependency confusion risk).

**CI** (no keyring): `pip install --index-url "https://oauth2accesstoken:$(gcloud auth print-access-token)@<LOCATION>-python.pkg.dev/<PROJECT>/<REPOSITORY>/simple/" infimatrix-nova-sdk`
(token valid 60 minutes; never commit it).

## 3. Use

```bash
export NOVA_BASE_URL=https://api.example.com NOVA_API_KEY=nova_key_... NOVA_TENANT_ID=<uuid>
```

```python
from nova_sdk import NovaClient

with NovaClient() as nova:                       # reads NOVA_* variables
    email = nova.emails.send(
        recipient_email="ada@example.com", subject="Welcome!", html_content="<h1>Hi</h1>",
    )
    print(email.message_id, email.status)
```

Async:

```python
import asyncio
from nova_sdk.aio import AsyncNovaClient

async def main():
    async with AsyncNovaClient() as nova:
        print(await nova.health())

asyncio.run(main())
```

Errors derive from `nova_sdk.exceptions`; see [error handling](error-handling.md), [authentication](authentication.md)
and [conventions](conventions.md). Only idempotent requests are retried.
