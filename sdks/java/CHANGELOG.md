# Changelog

All notable changes to the Nova Java SDK (`com.infimatrix:nova-sdk`) are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.2.0] - Unreleased

### Added
- `tenants().currentTenantId()` returns the tenant the credentials resolve to (client default, otherwise `GET /auth/me/`).
- `TemplateRenderResult` (`subject()`, `htmlContent()`), and `secret()`, `secretMasked()`, `createdAt()`, `updatedAt()` on
  `WebhookEndpointCreateUpdate`, `message()` on `Logout`. These fields were silently dropped before because the contract did
  not declare them; the corrections are kept in `openapi/sdk-overlay.yaml` until the backend contract is fixed.
- First version of the Java SDK for Java 17+ (JDK `java.net.http` client, Jackson for JSON).
- `NovaClient` with an immutable, thread-safe design and API classes for auth, users, tenants and memberships,
  templates, contacts and groups, emails and logs, providers, webhooks, campaigns, analytics, audit logs and the
  media library.
- Immutable `record` models and request builders generated from `openapi/nova-api.yaml`
  (`scripts/gen_java_models.py`).
- Auto-paginating `Page`, multipart uploads (`FileUpload`), CSV exports.
- Typed unchecked exceptions, bounded retries for idempotent requests only, `Retry-After` support, timeouts,
  redirect protection and secret redaction.
- Contract test that exercises every operation and validates each request against the OpenAPI document.

### Changed
- Workspace operations that put the tenant in the URL (`tenants().get/update`, `tenants().memberships()`) no longer require a
  tenant id: with only a server URL and an API key the SDK asks the server which tenant the credentials belong to.
  `tenants().delete()` still requires an explicit id. `templates().render()` now returns `TemplateRenderResult`
  (it returned an empty `TemplateRender`).

### Fixed
- Credentials are now fully stripped from the `Location` reported by a redirect error when the password itself contains
  `@` (the whole `user:se@cret@` used to be reported because `java.net.URI` parses it as a registry authority).
  Found by mutation testing.
- Path identifiers `.` and `..` are rejected with `NovaClientValidationException` instead of being sent as a raw dot-segment
  that servers and proxies normalise away (so `templates().get("..")` addressed `/api/v1/`). Found by the cross-language conformance suite.
- A 2xx response that declares a JSON content type but carries an invalid body now raises `NovaApiException`
  (`errorCode()` `INVALID_RESPONSE`) instead of returning the raw text as if the call had succeeded. Non-JSON content
  types (CSV, downloads, proxies) are unchanged.

