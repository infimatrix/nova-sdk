"""Main unified NovaClient interface for the Nova Python SDK."""

from __future__ import annotations

import uuid
from collections.abc import Callable, Generator, Iterator, Mapping
from contextlib import contextmanager
from typing import Any

import httpx

from nova_sdk.config import NovaConfig, _clean_credential, _sanitize_secret
from nova_sdk.exceptions import NovaValidationError
from nova_sdk.http import HTTPTransport
from nova_sdk.models import ApiResponse, PaginatedResponse
from nova_sdk.pagination import iter_items, iter_pages
from nova_sdk.resources import (
    AnalyticsResource,
    AssetsResource,
    AuditResource,
    AuthResource,
    CampaignsResource,
    ContactsResource,
    EmailsResource,
    ProvidersResource,
    TemplatesResource,
    TenantsResource,
    UsersResource,
    WebhooksResource,
)


def build_config(
    *,
    config: NovaConfig | None,
    base_url: str | None,
    api_key: str | None,
    access_token: str | None,
    tenant_id: str | None,
    timeout: float,
    max_retries: int,
    retry_backoff_factor: float,
    retry_jitter: bool,
    verify_ssl: bool,
    default_headers: Mapping[str, str] | None,
) -> NovaConfig:
    """Resolve a validated NovaConfig from either an explicit config or keyword options."""
    if config is not None:
        return config
    kwargs: dict[str, Any] = {
        "timeout": timeout,
        "max_retries": max_retries,
        "retry_backoff_factor": retry_backoff_factor,
        "retry_jitter": retry_jitter,
        "verify_ssl": verify_ssl,
        "default_headers": dict(default_headers or {}),
    }
    if base_url is not None:
        kwargs["base_url"] = base_url
    if api_key is not None:
        kwargs["api_key"] = api_key
    if access_token is not None:
        kwargs["access_token"] = access_token
    if tenant_id is not None:
        kwargs["tenant_id"] = tenant_id
    return NovaConfig(**kwargs)


class NovaClient:
    """Official synchronous client for communicating with the Nova REST API.

    Example usage:
        from nova_sdk import NovaClient

        # Using an API Key:
        client = NovaClient(api_key="nova_key_...", base_url="http://localhost:8000")

        # Or using a context manager:
        with NovaClient(api_key="nova_key_...", tenant_id="...") as client:
            health = client.health()
            print("Server status:", health)
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        access_token: str | None = None,
        tenant_id: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_factor: float = 0.5,
        retry_jitter: bool = True,
        verify_ssl: bool = True,
        default_headers: Mapping[str, str] | None = None,
        config: NovaConfig | None = None,
        _http_client: httpx.Client | None = None,
    ) -> None:
        self._config = build_config(
            config=config,
            base_url=base_url,
            api_key=api_key,
            access_token=access_token,
            tenant_id=tenant_id,
            timeout=timeout,
            max_retries=max_retries,
            retry_backoff_factor=retry_backoff_factor,
            retry_jitter=retry_jitter,
            verify_ssl=verify_ssl,
            default_headers=default_headers,
        )

        self._transport = HTTPTransport(self._config, client=_http_client)
        self.auth = AuthResource(self._transport, self)
        self.tenants = TenantsResource(self._transport, self)
        self.templates = TemplatesResource(self._transport, self)
        self.contacts = ContactsResource(self._transport, self)
        self.emails = EmailsResource(self._transport, self)
        self.providers = ProvidersResource(self._transport, self)
        self.webhooks = WebhooksResource(self._transport, self)
        self.analytics = AnalyticsResource(self._transport, self)
        self.campaigns = CampaignsResource(self._transport, self)
        self.audit = AuditResource(self._transport, self)
        self.users = UsersResource(self._transport)
        self.assets = AssetsResource(self._transport, self)

    @property
    def config(self) -> NovaConfig:
        """Access the client's current configuration object."""
        return self._config

    @property
    def transport(self) -> HTTPTransport:
        """Internal transport instance."""
        return self._transport

    @property
    def tenant_id(self) -> str | None:
        """Return the current active tenant ID context."""
        return self._config.tenant_id

    def set_tenant_id(self, tenant_id: str | None) -> None:
        """Explicitly update the active tenant context for subsequent requests.

        Args:
            tenant_id: A valid UUID string, or None to clear tenant context.
        """
        if tenant_id is not None:
            try:
                self._config.tenant_id = str(uuid.UUID(str(tenant_id).strip()))
            except ValueError as exc:
                raise NovaValidationError(
                    f"tenant_id must be a valid UUID string, got {tenant_id!r}."
                ) from exc
        else:
            self._config.tenant_id = None

    @contextmanager
    def with_tenant(self, tenant_id: str) -> Generator[NovaClient, None, None]:
        """Temporarily switch tenant context for the duration of a context block.

        Restores the previous tenant context safely upon exit.
        """
        previous_tenant_id = self._config.tenant_id
        self.set_tenant_id(tenant_id)
        try:
            yield self
        finally:
            self._config.tenant_id = previous_tenant_id

    def set_auth_token(self, access_token: str | None) -> None:
        """Update or clear the active JWT access token."""
        self._config.access_token = _clean_credential(access_token)

    def set_api_key(self, api_key: str | None) -> None:
        """Update or clear the active API key."""
        self._config.api_key = _clean_credential(api_key)

    @staticmethod
    def iter_pages(
        fetch: Callable[..., PaginatedResponse[Any]], /, **kwargs: Any
    ) -> Iterator[PaginatedResponse[Any]]:
        """Yield pages from a list method, e.g. ``client.iter_pages(client.contacts.list)``."""
        return iter_pages(fetch, **kwargs)

    @staticmethod
    def iter_items(
        fetch: Callable[..., PaginatedResponse[Any]], /, **kwargs: Any
    ) -> Iterator[Any]:
        """Yield every item across all pages of a list method."""
        return iter_items(fetch, **kwargs)

    def health(self) -> dict[str, Any]:
        """Retrieve system health and database connectivity status.

        Endpoint: GET /api/v1/health/
        """
        response: ApiResponse[dict[str, Any]] = self._transport.request(
            "GET", "health/"
        )
        return response.data

    def close(self) -> None:
        """Close the underlying HTTP client and connection pool."""
        self._transport.close()

    def __enter__(self) -> NovaClient:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return (
            f"NovaClient("
            f"base_url={self._config.base_url!r}, "
            f"api_key={_sanitize_secret(self._config.api_key)}, "
            f"access_token={_sanitize_secret(self._config.access_token)}, "
            f"tenant_id={self._config.tenant_id!r})"
        )
