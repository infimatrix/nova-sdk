"""Asynchronous NovaClient for the Nova Python SDK."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from typing import Any

import httpx

from nova_sdk.aio.http import AsyncHTTPTransport
from nova_sdk.aio.resources import (
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
from nova_sdk.client import build_config
from nova_sdk.config import NovaConfig, _clean_credential, _sanitize_secret
from nova_sdk.exceptions import NovaValidationError
from nova_sdk.models import ApiResponse, PaginatedResponse
from nova_sdk.pagination import MAX_PAGES


class AsyncNovaClient:
    """Asynchronous client for the Nova REST API (``asyncio`` / ``httpx.AsyncClient``).

    Mirrors :class:`nova_sdk.NovaClient`: the same resources and methods, awaited.

    Example::

        async with AsyncNovaClient(api_key="nova_key_...") as client:
            page = await client.contacts.list(page_size=50)
            async for contact in client.iter_items(client.contacts.list):
                print(contact.email)

    Tenant context: one client instance may serve many concurrent tasks, so prefer
    passing ``tenant_id=`` per call over mutating the shared tenant with
    :meth:`set_tenant_id`.
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
        _http_client: httpx.AsyncClient | None = None,
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
        self._transport = AsyncHTTPTransport(self._config, client=_http_client)
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
        """The client's configuration object."""
        return self._config

    @property
    def transport(self) -> AsyncHTTPTransport:
        """Internal transport instance."""
        return self._transport

    @property
    def tenant_id(self) -> str | None:
        """The current default tenant ID."""
        return self._config.tenant_id

    def set_tenant_id(self, tenant_id: str | None) -> None:
        """Set the default tenant for subsequent requests (shared across tasks)."""
        if tenant_id is not None:
            try:
                self._config.tenant_id = str(uuid.UUID(str(tenant_id).strip()))
            except ValueError as exc:
                raise NovaValidationError(
                    f"tenant_id must be a valid UUID string, got {tenant_id!r}."
                ) from exc
        else:
            self._config.tenant_id = None

    def set_auth_token(self, access_token: str | None) -> None:
        """Update or clear the active JWT access token."""
        self._config.access_token = _clean_credential(access_token)

    def set_api_key(self, api_key: str | None) -> None:
        """Update or clear the active API key."""
        self._config.api_key = _clean_credential(api_key)

    async def health(self) -> dict[str, Any]:
        """Retrieve system health and database connectivity status.

        Endpoint: GET /api/v1/health/
        """
        response: ApiResponse[dict[str, Any]] = await self._transport.request(
            "GET", "health/"
        )
        return response.data

    @staticmethod
    async def iter_pages(
        fetch: Callable[..., Awaitable[PaginatedResponse[Any]]], /, **kwargs: Any
    ) -> AsyncIterator[PaginatedResponse[Any]]:
        """Yield pages from an async list method, e.g. ``client.contacts.list``."""
        page_number = kwargs.pop("page", None)
        if page_number is None:
            page_number = 1
        if not isinstance(page_number, int) or page_number < 1:
            raise NovaValidationError("page must be a positive integer.")
        for _ in range(MAX_PAGES):
            result = await fetch(page=page_number, **kwargs)
            yield result
            if not result.has_next or page_number >= result.pagination.total_pages:
                return
            page_number += 1

    @staticmethod
    async def iter_items(
        fetch: Callable[..., Awaitable[PaginatedResponse[Any]]], /, **kwargs: Any
    ) -> AsyncIterator[Any]:
        """Yield every item across all pages of an async list method."""
        async for page in AsyncNovaClient.iter_pages(fetch, **kwargs):
            for item in page.items:
                yield item

    async def aclose(self) -> None:
        """Close the underlying HTTP client and connection pool."""
        await self._transport.aclose()

    async def __aenter__(self) -> AsyncNovaClient:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.aclose()

    def __repr__(self) -> str:
        return (
            f"AsyncNovaClient("
            f"base_url={self._config.base_url!r}, "
            f"api_key={_sanitize_secret(self._config.api_key)}, "
            f"access_token={_sanitize_secret(self._config.access_token)}, "
            f"tenant_id={self._config.tenant_id!r})"
        )
