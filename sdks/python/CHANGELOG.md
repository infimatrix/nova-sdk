# Changelog

All notable changes to the Nova Python SDK are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.2.0] - Unreleased

### Added
- `AsyncNovaClient` (`nova_sdk.aio`) with the same resources as `NovaClient`, generated from the
  synchronous sources by `scripts/gen_python_async.py`.
- Typed response models (`nova_sdk.schemas`) generated from `openapi/nova-api.yaml` by
  `scripts/gen_python_models.py`. Models are dataclasses that also implement `Mapping`, and keep the
  complete payload in `.raw`.
- `client.auth.register()`, `forgot_password()`, `validate_reset_token()`, `reset_password()`,
  `change_password()`.
- `client.users` (`list`, `me`) and `client.assets` (`folders`, `files` including multipart upload).
- Pagination helpers `iter_pages()` / `iter_items()` (sync and async) and `PaginatedResponse.has_next`.
- `LICENSE` file, `CHANGELOG.md`, single-sourced version (`nova_sdk/_version.py`).

### Fixed
- Public return types of `tenants.list_members`, `contacts.list_groups`, `campaigns.list`, `auth.list_api_keys` and
  `audit.list` now name their model types instead of `dict`.
- The async resources use an async-typed base class, so `mypy` passes cleanly on the whole package.

### Changed
- Resource methods return typed models instead of `dict`. Models support `[]`, `.get()`, `in`,
  iteration and equality with dicts; `isinstance(x, dict)` is no longer true (use `x.to_dict()`).
- Path identifiers are URL-encoded, so an id can no longer alter the request path or query string.
- Legacy non-enveloped error bodies such as `{"error": "..."}` now produce a readable message.
- Build requires `setuptools>=77` (SPDX `license` expression).
- `HTTPTransport` shares request/response handling with the new async transport through `TransportCore`.

## [0.1.0]

- Initial release: `NovaClient`, resource clients, retries, typed exceptions.
