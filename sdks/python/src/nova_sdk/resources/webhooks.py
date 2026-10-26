"""Webhook Endpoint Subscriptions resource client for Nova SDK."""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from nova_sdk._model_base import parse_model
from nova_sdk.exceptions import NovaValidationError
from nova_sdk.models import PaginatedResponse, WebhookEvent
from nova_sdk.resources.base import BaseResource
from nova_sdk.schemas import (
    WebhookEndpoint,
    WebhookEndpointCreateUpdate,
    WebhookSecretRotation,
    WebhookTestDispatch,
)

if TYPE_CHECKING:
    from nova_sdk.client import NovaClient
    from nova_sdk.http import HTTPTransport


class WebhooksResource(BaseResource):
    """Resource client for managing tenant-scoped webhook endpoint subscriptions."""

    def __init__(
        self,
        transport: HTTPTransport,
        client: NovaClient | None = None,
    ) -> None:
        super().__init__(transport)
        self._client = client

    def list(
        self,
        *,
        search: str | None = None,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        params: Mapping[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[WebhookEndpoint]:
        """List webhook subscriptions for the active or specified tenant.

        Endpoint: GET /api/v1/webhooks/

        Args:
            search: Search across name and url fields.
            ordering: Sort field (e.g. 'name', 'created_at', '-created_at').
            page: Specific page number.
            page_size: Number of records per page.
            params: Additional raw query parameters.
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            PaginatedResponse of webhook endpoint records.
        """
        query_params: dict[str, Any] = dict(params or {})
        if search is not None:
            query_params["search"] = search
        if ordering is not None:
            query_params["ordering"] = ordering
        if page is not None:
            query_params["page"] = page
        if page_size is not None:
            query_params["page_size"] = page_size

        response = self._transport.request(
            "GET",
            "webhooks/",
            params=query_params or None,
            tenant_id=tenant_id,
        )
        return PaginatedResponse.from_response(
            response, item_parser=WebhookEndpoint.from_dict
        )

    def get(
        self,
        webhook_id: str,
        *,
        tenant_id: str | None = None,
    ) -> WebhookEndpoint:
        """Retrieve details of a specific webhook endpoint subscription.

        Endpoint: GET /api/v1/webhooks/{id}/

        Args:
            webhook_id: Webhook subscription UUID.
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            Dictionary containing webhook subscription attributes.

        Raises:
            NovaValidationError: If webhook_id is missing or empty.
            NovaNotFoundError: If the webhook subscription does not exist.
        """
        if not webhook_id or not str(webhook_id).strip():
            raise NovaValidationError("webhook_id must be a non-empty string.")
        clean_id = quote(str(webhook_id).strip(), safe="")

        response = self._transport.request(
            "GET",
            f"webhooks/{clean_id}/",
            tenant_id=tenant_id,
        )
        return parse_model(WebhookEndpoint, response.data or {})

    def create(
        self,
        *,
        name: str,
        url: str,
        events: Sequence[str] | None = None,
        is_active: bool = True,
        tenant_id: str | None = None,
    ) -> WebhookEndpointCreateUpdate:
        """Create a new webhook endpoint subscription in the tenant workspace.

        Endpoint: POST /api/v1/webhooks/

        .. note::
            Webhook creation generates a unique HMAC signing key (`secret`) prefixed
            with `whsec_` that is returned in the response. Webhook creation is a
            non-idempotent operation and is never automatically retried by the SDK.

        Args:
            name: Human-readable subscription name (required).
            url: Destination HTTPS callback URL (required).
            events: Optional list of event keys to subscribe to
                (e.g. `[WebhookEvent.EMAIL_DELIVERED, WebhookEvent.EMAIL_BOUNCED]`).
            is_active: Whether the webhook is enabled for event delivery (default True).
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            Dictionary representation of the created webhook subscription.

        Raises:
            NovaValidationError: If required fields are missing or event choices are invalid.
            NovaAPIError: If the server rejects the request.
        """
        if not name or not isinstance(name, str) or not name.strip():
            raise NovaValidationError("name must be a non-empty string.")
        if not url or not isinstance(url, str) or not url.strip():
            raise NovaValidationError("url must be a non-empty string.")

        payload: dict[str, Any] = {
            "name": name.strip(),
            "url": url.strip(),
            "is_active": bool(is_active),
        }

        if events is not None:
            if not isinstance(events, (list, tuple, set)):
                raise NovaValidationError(
                    "events must be a sequence of event key strings."
                )
            payload["events"] = [str(e).strip() for e in events]

        response = self._transport.request(
            "POST",
            "webhooks/",
            json=payload,
            tenant_id=tenant_id,
            allow_retry=False,
        )
        return parse_model(WebhookEndpointCreateUpdate, response.data or {})

    def update(
        self,
        webhook_id: str,
        *,
        name: str | None = None,
        url: str | None = None,
        events: Sequence[str] | None = None,
        is_active: bool | None = None,
        tenant_id: str | None = None,
    ) -> WebhookEndpointCreateUpdate:
        """Partially update an existing webhook subscription.

        Endpoint: PATCH /api/v1/webhooks/{id}/

        .. note::
            Webhook update is a non-idempotent operation and is never
            automatically retried by the SDK.

        Args:
            webhook_id: Webhook subscription UUID.
            name: Updated subscription name.
            url: Updated destination callback URL.
            events: Updated list of subscribed event keys.
            is_active: Updated active status flag.
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            Dictionary representation of the updated webhook subscription.

        Raises:
            NovaValidationError: If webhook_id is missing or parameters are invalid.
            NovaAPIError: If the server rejects the update payload.
        """
        if not webhook_id or not str(webhook_id).strip():
            raise NovaValidationError("webhook_id must be a non-empty string.")
        clean_id = quote(str(webhook_id).strip(), safe="")

        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name.strip()
        if url is not None:
            payload["url"] = url.strip()
        if events is not None:
            if not isinstance(events, (list, tuple, set)):
                raise NovaValidationError(
                    "events must be a sequence of event key strings."
                )
            payload["events"] = [str(e).strip() for e in events]
        if is_active is not None:
            payload["is_active"] = bool(is_active)

        response = self._transport.request(
            "PATCH",
            f"webhooks/{clean_id}/",
            json=payload,
            tenant_id=tenant_id,
            allow_retry=False,
        )
        return parse_model(WebhookEndpointCreateUpdate, response.data or {})

    def delete(
        self,
        webhook_id: str,
        *,
        tenant_id: str | None = None,
    ) -> None:
        """Delete a webhook endpoint subscription from the tenant workspace.

        Endpoint: DELETE /api/v1/webhooks/{id}/

        .. note::
            Webhook deletion has external side effects and is never
            automatically retried by the SDK.

        Args:
            webhook_id: Webhook subscription UUID.
            tenant_id: Optional explicit tenant UUID override.

        Raises:
            NovaValidationError: If webhook_id is missing or empty.
            NovaNotFoundError: If the webhook subscription does not exist.
        """
        if not webhook_id or not str(webhook_id).strip():
            raise NovaValidationError("webhook_id must be a non-empty string.")
        clean_id = quote(str(webhook_id).strip(), safe="")

        self._transport.request(
            "DELETE",
            f"webhooks/{clean_id}/",
            tenant_id=tenant_id,
            allow_retry=False,
        )

    def events(
        self,
        *,
        tenant_id: str | None = None,
    ) -> builtins.list[dict[str, Any]]:
        """List all supported webhook event subscription choices and descriptions.

        Endpoint: GET /api/v1/webhooks/events/

        Args:
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            List of event definition dictionaries with 'key' and 'label'.
        """
        response = self._transport.request(
            "GET",
            "webhooks/events/",
            tenant_id=tenant_id,
        )
        if isinstance(response.data, list):
            return response.data
        return []

    def rotate_secret(
        self,
        webhook_id: str,
        *,
        tenant_id: str | None = None,
    ) -> WebhookSecretRotation:
        """Generate and rotate a new HMAC signing secret for a webhook endpoint.

        Endpoint: POST /api/v1/webhooks/{id}/rotate-secret/

        .. warning::
            Rotating the secret immediately invalidates the previous HMAC signing key
            in the database. Any subscriber applications verifying incoming payloads
            with the old secret will fail validation until updated with the new secret.
            This operation is non-idempotent and is never automatically retried by the SDK.

        Args:
            webhook_id: Webhook subscription UUID.
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            Dictionary containing:
            - `secret`: Newly generated raw HMAC secret (`whsec_...`).
            - `message`: Confirmation message.

        Raises:
            NovaValidationError: If webhook_id is missing or empty.
            NovaAPIError: If the server rejects the rotation request.
        """
        if not webhook_id or not str(webhook_id).strip():
            raise NovaValidationError("webhook_id must be a non-empty string.")
        clean_id = quote(str(webhook_id).strip(), safe="")

        response = self._transport.request(
            "POST",
            f"webhooks/{clean_id}/rotate-secret/",
            tenant_id=tenant_id,
            allow_retry=False,
        )
        return parse_model(WebhookSecretRotation, response.data or {})

    def test(
        self,
        webhook_id: str,
        *,
        event_type: str = WebhookEvent.EMAIL_DELIVERED,
        tenant_id: str | None = None,
    ) -> WebhookTestDispatch:
        """Dispatch a test webhook event payload to the subscriber endpoint URL.

        Endpoint: POST /api/v1/webhooks/{id}/send-test/

        .. warning::
            This operation enqueues an asynchronous Celery task that sends a real
            test HTTP POST payload to the configured webhook callback URL.
            Side-effect operations are never automatically retried by the SDK.
            Unit tests must always use mocks and avoid triggering calls to live URLs.

        Args:
            webhook_id: Webhook subscription UUID (required).
            event_type: Event type key for test payload (default 'email.delivered').
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            Dictionary containing test dispatch results:
            - `success`: Boolean confirmation flag.
            - `message`: Human-readable dispatch message.
            - `webhook_id`: Webhook ID.
            - `task_id`: Celery background task UUID.
            - `url`: Destination callback URL.
            - `event_type`: Event type used for test payload.

        Raises:
            NovaValidationError: If webhook_id or event_type is missing or empty.
            NovaAPIError: If the server rejects the test dispatch request.
        """
        if not webhook_id or not str(webhook_id).strip():
            raise NovaValidationError("webhook_id must be a non-empty string.")
        if not event_type or not str(event_type).strip():
            raise NovaValidationError("event_type must be a non-empty string.")

        clean_id = quote(str(webhook_id).strip(), safe="")
        clean_event = str(event_type).strip()

        payload = {
            "event_type": clean_event,
        }

        response = self._transport.request(
            "POST",
            f"webhooks/{clean_id}/send-test/",
            json=payload,
            tenant_id=tenant_id,
            allow_retry=False,
        )
        return parse_model(WebhookTestDispatch, response.data or {})
