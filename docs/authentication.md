# Authentication and tenancy

## Credentials

Both SDKs send `Authorization: Bearer <credential>`.

| Credential | Source | Lifetime | Use for |
|---|---|---|---|
| API key `nova_key_…` | `auth.apiKeys.create` | until revoked / `expires_at` | server-to-server integrations (recommended) |
| JWT access token | `auth.login`, `auth.register` | short | user sessions; refresh with `auth.refresh` |

If both are configured the **API key wins**. Leading `Bearer ` prefixes and whitespace are stripped.
SDKs do not refresh tokens automatically: call `auth.refresh(refreshToken)` and set the new token
(`set_auth_token` in Python, `setAccessToken` in TypeScript), or pass `set_current_token` / `setCurrentToken`
to `login`/`register` to store the access token on the client.

## Tenancy

A user can belong to several tenants (workspaces). The SDK sends `X-Tenant-ID`:

- from the client default (`tenant_id` / `tenantId` option or `NOVA_TENANT_ID`), or
- per call (`tenant_id=` / `{ tenantId }`), which overrides the default.

If the header is omitted the server uses the caller's first active membership. If it names a tenant the
caller does not belong to, tenant-scoped endpoints fail with 403/400. Tenant IDs are validated as UUIDs
client-side.

Concurrency: mutating the shared default tenant (`set_tenant_id` / `setTenantId`) affects every in-flight task
using the client. Prefer per-call overrides, or in TypeScript `client.withTenant(id)`, which returns an
independent client.

## Handling secrets

- Credentials are redacted in `repr`/`toString`, `JSON.stringify`, `util.inspect`, logs and exception messages.
- Redirects are never followed, so credentials cannot leak to another host. A 3xx raises `NovaRedirectError`
  with credentials stripped from the reported location.
- TLS verification is on by default (Python: `verify_ssl`). Use `https://` outside local development.
- Rotate API keys by creating a new one and revoking the old one.

## Never ship credentials to browsers

An API key or token in front-end code can be read by every visitor and grants access to a tenant's contacts and
the ability to send email as that tenant. The TypeScript SDK therefore refuses to construct a credentialed client
in a browser unless `dangerouslyAllowBrowser: true` is set. Put a server in between.
