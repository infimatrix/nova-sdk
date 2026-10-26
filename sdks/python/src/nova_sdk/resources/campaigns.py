"""Campaigns and Transactional Notifications resource clients for Nova SDK."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from nova_sdk._model_base import parse_model
from nova_sdk.exceptions import NovaValidationError
from nova_sdk.models import PaginatedResponse
from nova_sdk.resources.base import BaseResource
from nova_sdk.schemas import TransactionalNotification, TransactionalTestDispatch

if TYPE_CHECKING:
    from nova_sdk.client import NovaClient
    from nova_sdk.http import HTTPTransport


class TransactionalNotificationsResource(BaseResource):
    """Resource client for managing tenant-scoped transactional email notification mappings.

    Transactional notifications map application events (e.g. 'welcome_email',
    'password_reset') via an api_identifier to email templates and provide
    test email dispatch capabilities.
    """

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
    ) -> PaginatedResponse[TransactionalNotification]:
        """List transactional notifications for the active or specified tenant.

        Endpoint: GET /api/v1/campaigns/transactional/

        Args:
            search: Search query across display_id, name, api_identifier, and description.
            ordering: Sort field (e.g. 'created_at', 'display_id', 'name'; prefix with '-' for desc).
            page: Specific page number.
            page_size: Number of records per page.
            params: Additional raw query parameters.
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            PaginatedResponse of transactional notification records.
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
            "campaigns/transactional/",
            params=query_params or None,
            tenant_id=tenant_id,
            allow_retry=True,
        )
        return PaginatedResponse.from_response(
            response, item_parser=TransactionalNotification.from_dict
        )

    def get(
        self,
        notification_id: str,
        *,
        tenant_id: str | None = None,
    ) -> TransactionalNotification:
        """Retrieve details of a specific transactional notification.

        Endpoint: GET /api/v1/campaigns/transactional/{id}/

        Args:
            notification_id: Transactional notification UUID.
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            Dictionary containing notification attributes.

        Raises:
            NovaValidationError: If notification_id is missing or empty.
            NovaNotFoundError: If the notification does not exist.
        """
        if not notification_id or not str(notification_id).strip():
            raise NovaValidationError("notification_id must be a non-empty string.")
        clean_id = quote(str(notification_id).strip(), safe="")

        response = self._transport.request(
            "GET",
            f"campaigns/transactional/{clean_id}/",
            tenant_id=tenant_id,
            allow_retry=True,
        )
        return parse_model(TransactionalNotification, response.data)

    def create(
        self,
        *,
        name: str,
        api_identifier: str,
        template_id: str | None = None,
        description: str | None = None,
        tenant_id: str | None = None,
    ) -> TransactionalNotification:
        """Create a new transactional notification mapping.

        Endpoint: POST /api/v1/campaigns/transactional/

        Note:
            Side-effecting call: automatic retry on failure is disabled (allow_retry=False).

        Args:
            name: Human-readable notification name (e.g. 'Welcome Email').
            api_identifier: Unique API trigger key (e.g. 'welcome_email').
                Backend normalizes dashes to underscores and enforces per-tenant uniqueness.
            template_id: Optional UUID of the linked Template.
            description: Optional explanation of when this notification is triggered.
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            Dictionary containing created notification attributes.

        Raises:
            NovaValidationError: If required fields are missing or invalid.
            NovaAPIError: If creation fails or duplicate api_identifier exists.
        """
        if not name or not str(name).strip():
            raise NovaValidationError("name must be a non-empty string.")
        if not api_identifier or not str(api_identifier).strip():
            raise NovaValidationError("api_identifier must be a non-empty string.")

        payload: dict[str, Any] = {
            "name": str(name).strip(),
            "api_identifier": str(api_identifier).strip(),
        }
        if template_id is not None:
            payload["template_id"] = str(template_id).strip() if template_id else None
        if description is not None:
            payload["description"] = str(description).strip()

        response = self._transport.request(
            "POST",
            "campaigns/transactional/",
            json=payload,
            tenant_id=tenant_id,
            allow_retry=False,
        )
        return parse_model(TransactionalNotification, response.data)

    def update(
        self,
        notification_id: str,
        *,
        name: str | None = None,
        api_identifier: str | None = None,
        template_id: str | None = None,
        description: str | None = None,
        tenant_id: str | None = None,
    ) -> TransactionalNotification:
        """Partially update a transactional notification mapping.

        Endpoint: PATCH /api/v1/campaigns/transactional/{id}/

        Note:
            Side-effecting call: automatic retry on failure is disabled (allow_retry=False).

        Args:
            notification_id: Transactional notification UUID.
            name: Optional updated name.
            api_identifier: Optional updated API trigger key.
            template_id: Optional updated Template UUID (pass empty string or None to unlink).
            description: Optional updated description.
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            Dictionary containing updated notification attributes.

        Raises:
            NovaValidationError: If notification_id is invalid or no fields provided.
            NovaNotFoundError: If the notification does not exist.
        """
        if not notification_id or not str(notification_id).strip():
            raise NovaValidationError("notification_id must be a non-empty string.")
        clean_id = quote(str(notification_id).strip(), safe="")

        payload: dict[str, Any] = {}
        if name is not None:
            if not str(name).strip():
                raise NovaValidationError("name must be a non-empty string.")
            payload["name"] = str(name).strip()
        if api_identifier is not None:
            if not str(api_identifier).strip():
                raise NovaValidationError("api_identifier must be a non-empty string.")
            payload["api_identifier"] = str(api_identifier).strip()
        if template_id is not None:
            payload["template_id"] = str(template_id).strip() if template_id else None
        if description is not None:
            payload["description"] = str(description).strip()

        if not payload:
            raise NovaValidationError("At least one field must be provided to update.")

        response = self._transport.request(
            "PATCH",
            f"campaigns/transactional/{clean_id}/",
            json=payload,
            tenant_id=tenant_id,
            allow_retry=False,
        )
        return parse_model(TransactionalNotification, response.data)

    def delete(
        self,
        notification_id: str,
        *,
        tenant_id: str | None = None,
    ) -> None:
        """Delete a transactional notification mapping.

        Endpoint: DELETE /api/v1/campaigns/transactional/{id}/

        Note:
            Side-effecting call: automatic retry on failure is disabled (allow_retry=False).

        Args:
            notification_id: Transactional notification UUID to delete.
            tenant_id: Optional explicit tenant UUID override.

        Raises:
            NovaValidationError: If notification_id is missing or empty.
            NovaNotFoundError: If the notification does not exist.
        """
        if not notification_id or not str(notification_id).strip():
            raise NovaValidationError("notification_id must be a non-empty string.")
        clean_id = quote(str(notification_id).strip(), safe="")

        self._transport.request(
            "DELETE",
            f"campaigns/transactional/{clean_id}/",
            tenant_id=tenant_id,
            allow_retry=False,
        )

    def send_test(
        self,
        notification_id: str,
        *,
        recipient_email: str,
        from_name: str | None = None,
        sender_email: str | None = None,
        provider_id: str | None = None,
        cc_emails: str | None = None,
        bcc_emails: str | None = None,
        reply_to: str | None = None,
        tenant_id: str | None = None,
    ) -> TransactionalTestDispatch:
        """Dispatch a test email for this transactional notification.

        Endpoint: POST /api/v1/campaigns/transactional/{id}/send-test/

        Note:
            Side-effecting call: this triggers actual asynchronous email dispatch
            via Celery worker tasks. Automatic retry on failure is strictly
            disabled (allow_retry=False).

        Args:
            notification_id: Transactional notification UUID.
            recipient_email: Destination recipient email address.
            from_name: Optional custom sender name (defaults to tenant name or 'Support').
            sender_email: Optional custom sender email (defaults to 'admin@company.com').
            provider_id: Optional delivery Provider UUID to route dispatch through.
            cc_emails: Optional comma-separated CC recipients.
            bcc_emails: Optional comma-separated BCC recipients.
            reply_to: Optional Reply-To address.
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            Dictionary containing confirmation message, message_id, and email_id.

        Raises:
            NovaValidationError: If notification_id or recipient_email is missing/invalid.
            NovaNotFoundError: If the notification does not exist.
        """
        if not notification_id or not str(notification_id).strip():
            raise NovaValidationError("notification_id must be a non-empty string.")
        clean_id = quote(str(notification_id).strip(), safe="")

        if (
            not recipient_email
            or not str(recipient_email).strip()
            or "@" not in str(recipient_email)
        ):
            raise NovaValidationError(
                "recipient_email must be a valid non-empty email address."
            )

        payload: dict[str, Any] = {
            "recipient_email": str(recipient_email).strip(),
        }
        if from_name is not None:
            payload["from_name"] = str(from_name).strip()
        if sender_email is not None:
            clean_sender = str(sender_email).strip()
            if clean_sender and "@" not in clean_sender:
                raise NovaValidationError("sender_email must be a valid email address.")
            payload["sender_email"] = clean_sender
        if provider_id is not None:
            payload["provider_id"] = str(provider_id).strip()
        if cc_emails is not None:
            payload["cc_emails"] = str(cc_emails).strip()
        if bcc_emails is not None:
            payload["bcc_emails"] = str(bcc_emails).strip()
        if reply_to is not None:
            payload["reply_to"] = str(reply_to).strip()

        response = self._transport.request(
            "POST",
            f"campaigns/transactional/{clean_id}/send-test/",
            json=payload,
            tenant_id=tenant_id,
            allow_retry=False,
        )
        return parse_model(TransactionalTestDispatch, response.data)


class CampaignsResource(BaseResource):
    """Resource client for Nova campaigns and transactional notification workflows.

    Provides access to transactional notification mappings via the
    `.transactional` sub-resource, as well as convenient top-level shortcuts.
    """

    def __init__(
        self,
        transport: HTTPTransport,
        client: NovaClient | None = None,
    ) -> None:
        super().__init__(transport)
        self._client = client
        self.transactional = TransactionalNotificationsResource(transport, client)

    def list(
        self,
        *,
        search: str | None = None,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        params: Mapping[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[TransactionalNotification]:
        """List transactional notifications (shortcut to .transactional.list)."""
        return self.transactional.list(
            search=search,
            ordering=ordering,
            page=page,
            page_size=page_size,
            params=params,
            tenant_id=tenant_id,
        )

    def get(
        self,
        notification_id: str,
        *,
        tenant_id: str | None = None,
    ) -> TransactionalNotification:
        """Retrieve a transactional notification (shortcut to .transactional.get)."""
        return self.transactional.get(
            notification_id,
            tenant_id=tenant_id,
        )

    def create(
        self,
        *,
        name: str,
        api_identifier: str,
        template_id: str | None = None,
        description: str | None = None,
        tenant_id: str | None = None,
    ) -> TransactionalNotification:
        """Create a transactional notification (shortcut to .transactional.create)."""
        return self.transactional.create(
            name=name,
            api_identifier=api_identifier,
            template_id=template_id,
            description=description,
            tenant_id=tenant_id,
        )

    def update(
        self,
        notification_id: str,
        *,
        name: str | None = None,
        api_identifier: str | None = None,
        template_id: str | None = None,
        description: str | None = None,
        tenant_id: str | None = None,
    ) -> TransactionalNotification:
        """Partially update a transactional notification (shortcut to .transactional.update)."""
        return self.transactional.update(
            notification_id,
            name=name,
            api_identifier=api_identifier,
            template_id=template_id,
            description=description,
            tenant_id=tenant_id,
        )

    def delete(
        self,
        notification_id: str,
        *,
        tenant_id: str | None = None,
    ) -> None:
        """Delete a transactional notification (shortcut to .transactional.delete)."""
        self.transactional.delete(
            notification_id,
            tenant_id=tenant_id,
        )

    def send_test(
        self,
        notification_id: str,
        *,
        recipient_email: str,
        from_name: str | None = None,
        sender_email: str | None = None,
        provider_id: str | None = None,
        cc_emails: str | None = None,
        bcc_emails: str | None = None,
        reply_to: str | None = None,
        tenant_id: str | None = None,
    ) -> TransactionalTestDispatch:
        """Send a test email for this notification (shortcut to .transactional.send_test)."""
        return self.transactional.send_test(
            notification_id,
            recipient_email=recipient_email,
            from_name=from_name,
            sender_email=sender_email,
            provider_id=provider_id,
            cc_emails=cc_emails,
            bcc_emails=bcc_emails,
            reply_to=reply_to,
            tenant_id=tenant_id,
        )
