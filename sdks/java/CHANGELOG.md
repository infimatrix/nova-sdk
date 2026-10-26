# Changelog

All notable changes to the Nova Java SDK (`com.infimatrix:nova-sdk`) are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - Unreleased

### Added
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
