# Changelog

All notable changes to `@infimatrix/nova-sdk` are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - Unreleased

### Added
- First release of the TypeScript/JavaScript SDK for Node.js 18.17+ (built-in `fetch`, zero runtime dependencies).
- `NovaClient` with resources for auth, users, tenants and memberships, templates, contacts and groups,
  emails and logs, providers, webhooks, campaigns, analytics, audit logs and the media library.
- Types for every API model, generated from `openapi/nova-api.yaml` (`scripts/gen_ts_types.py`).
- Auto-paginating `Page` results (`for await`), multipart uploads, CSV exports.
- Typed errors, bounded retries for idempotent requests only, `Retry-After` support, timeouts,
  `AbortSignal` cancellation, correlation IDs, redirect protection and secret redaction.
- ESM + CommonJS builds with bundled type declarations.

### Fixed
- Path identifiers `.` and `..` are rejected with `NovaValidationError` instead of being normalised away by the HTTP
  stack (which turned `templates.get("..")` into a request for `/api/v1/`). Found by the cross-language conformance suite.
- A 2xx response that declares a JSON content type but carries an invalid body now raises `NovaAPIError`
  (`errorCode: "INVALID_RESPONSE"`) instead of returning the raw text as if the call had succeeded. Non-JSON content
  types (CSV, downloads, proxies) are unchanged.

