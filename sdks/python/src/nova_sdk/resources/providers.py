"""Email Service Provider configuration resource client for Nova SDK."""

from __future__ import annotations

import builtins
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from nova_sdk._model_base import parse_model
from nova_sdk.exceptions import NovaValidationError
from nova_sdk.models import PaginatedResponse, ProviderType
from nova_sdk.resources.base import BaseResource
from nova_sdk.schemas import (
    ProviderConfiguration,
    ProviderConfigurationCreateUpdate,
    ProviderTestDispatch,
)

if TYPE_CHECKING:
    from nova_sdk.client import NovaClient
    from nova_sdk.http import HTTPTransport


class ProvidersResource(BaseResource):
    """Resource client for managing tenant-scoped email delivery provider configurations."""

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
    ) -> PaginatedResponse[ProviderConfiguration]:
        """List provider configurations for the active or specified tenant.

        Endpoint: GET /api/v1/providers/

        Args:
            search: Search across name, provider_type, smtp_host, and smtp_user.
            ordering: Sort field (e.g. 'priority', 'name', '-created_at').
            page: Specific page number.
            page_size: Number of records per page.
            params: Additional raw query parameters.
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            PaginatedResponse of provider configuration records.
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
            "providers/",
            params=query_params or None,
            tenant_id=tenant_id,
        )
        return PaginatedResponse.from_response(
            response, item_parser=ProviderConfiguration.from_dict
        )

    def get(
        self,
        provider_id: str,
        *,
        tenant_id: str | None = None,
    ) -> ProviderConfiguration:
        """Retrieve details of a specific provider configuration.

        Endpoint: GET /api/v1/providers/{id}/

        Args:
            provider_id: Provider configuration UUID.
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            Dictionary containing provider configuration attributes.
            Write-only credentials are never exposed; masked status flags
            `has_password` and `has_secret_key` indicate credential presence.

        Raises:
            NovaValidationError: If provider_id is missing or empty.
            NovaNotFoundError: If the provider configuration does not exist.
        """
        if not provider_id or not str(provider_id).strip():
            raise NovaValidationError("provider_id must be a non-empty string.")
        clean_id = quote(str(provider_id).strip(), safe="")

        response = self._transport.request(
            "GET",
            f"providers/{clean_id}/",
            tenant_id=tenant_id,
        )
        return parse_model(ProviderConfiguration, response.data or {})

    def create(
        self,
        *,
        name: str,
        provider_type: str = ProviderType.SMTP,
        senders: builtins.list[Mapping[str, Any]] | None = None,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        tls_enabled: bool | None = None,
        authentication_type: str | None = None,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        aws_region: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        rate_limit_per_minute: int | None = None,
        is_active: bool | None = None,
        priority: int | None = None,
        encrypted_credentials: Mapping[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> ProviderConfigurationCreateUpdate:
        """Create a new email provider integration in the tenant workspace.

        Endpoint: POST /api/v1/providers/

        .. note::
            Provider creation has external side effects and is never
            automatically retried by the SDK. Write-only credentials
            (`smtp_password`, `aws_secret_access_key`) are masked and
            never returned in API responses.

        Args:
            name: Human-readable integration name (required).
            provider_type: Provider integration type ('SMTP', 'AWS_SES', etc.).
            senders: Optional list of sender identity dicts:
                [{'name': 'Support', 'email': 'support@example.com', 'is_default': True}].
            smtp_host: Hostname or IP of the SMTP relay server.
            smtp_port: SMTP port number (default 587).
            tls_enabled: Whether to enforce STARTTLS encryption.
            authentication_type: Authentication mechanism ('BASIC', 'NONE', 'OAUTH2').
            smtp_user: SMTP authentication username.
            smtp_password: SMTP password or app password (write-only).
            aws_region: AWS SES Region (e.g. 'us-east-1').
            aws_access_key_id: AWS IAM Access Key ID.
            aws_secret_access_key: AWS IAM Secret Access Key (write-only).
            rate_limit_per_minute: Maximum messages allowed per minute (default 25).
            is_active: Whether this provider is enabled for delivery routing.
            priority: Routing priority order (lower number = higher priority).
            encrypted_credentials: Optional custom encrypted credentials mapping.
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            Dictionary representation of the created provider configuration.

        Raises:
            NovaValidationError: If validation fails for required parameters.
            NovaAPIError: If the server rejects the integration configuration.
        """
        if not name or not isinstance(name, str) or not name.strip():
            raise NovaValidationError("name must be a non-empty string.")
        if not provider_type or not str(provider_type).strip():
            raise NovaValidationError("provider_type must be a non-empty string.")

        payload: dict[str, Any] = {
            "name": name.strip(),
            "provider_type": str(provider_type).strip(),
        }

        if senders is not None:
            if not isinstance(senders, (list, tuple)):
                raise NovaValidationError(
                    "senders must be a list of sender dictionaries."
                )
            formatted_senders = []
            for idx, s in enumerate(senders):
                if not isinstance(s, Mapping):
                    raise NovaValidationError(
                        f"Each sender entry must be a dictionary, got {type(s).__name__} at index {idx}."
                    )
                if "email" not in s or not str(s["email"]).strip():
                    raise NovaValidationError(
                        f"Sender entry at index {idx} must contain a non-empty 'email' field."
                    )
                formatted_senders.append(dict(s))
            payload["senders"] = formatted_senders

        if smtp_host is not None:
            payload["smtp_host"] = str(smtp_host)
        if smtp_port is not None:
            payload["smtp_port"] = int(smtp_port)
        if tls_enabled is not None:
            payload["tls_enabled"] = bool(tls_enabled)
        if authentication_type is not None:
            payload["authentication_type"] = str(authentication_type)
        if smtp_user is not None:
            payload["smtp_user"] = str(smtp_user)
        if smtp_password is not None:
            payload["smtp_password"] = str(smtp_password)
        if aws_region is not None:
            payload["aws_region"] = str(aws_region)
        if aws_access_key_id is not None:
            payload["aws_access_key_id"] = str(aws_access_key_id)
        if aws_secret_access_key is not None:
            payload["aws_secret_access_key"] = str(aws_secret_access_key)
        if rate_limit_per_minute is not None:
            payload["rate_limit_per_minute"] = int(rate_limit_per_minute)
        if is_active is not None:
            payload["is_active"] = bool(is_active)
        if priority is not None:
            payload["priority"] = int(priority)
        if encrypted_credentials is not None:
            payload["encrypted_credentials"] = dict(encrypted_credentials)

        response = self._transport.request(
            "POST",
            "providers/",
            json=payload,
            tenant_id=tenant_id,
            allow_retry=False,
        )
        return parse_model(ProviderConfigurationCreateUpdate, response.data or {})

    def update(
        self,
        provider_id: str,
        *,
        name: str | None = None,
        provider_type: str | None = None,
        senders: builtins.list[Mapping[str, Any]] | None = None,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        tls_enabled: bool | None = None,
        authentication_type: str | None = None,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        aws_region: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        rate_limit_per_minute: int | None = None,
        is_active: bool | None = None,
        priority: int | None = None,
        encrypted_credentials: Mapping[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> ProviderConfigurationCreateUpdate:
        """Partially update an existing provider configuration.

        Endpoint: PATCH /api/v1/providers/{id}/

        .. note::
            Provider update has external side effects and is never
            automatically retried by the SDK.

        Args:
            provider_id: Provider configuration UUID.
            name: Updated integration name.
            provider_type: Updated provider type.
            senders: Updated list of sender identities.
            smtp_host: Updated SMTP relay hostname.
            smtp_port: Updated SMTP port number.
            tls_enabled: Updated TLS flag.
            authentication_type: Updated authentication mechanism.
            smtp_user: Updated SMTP username.
            smtp_password: Updated SMTP password (write-only).
            aws_region: Updated AWS SES region.
            aws_access_key_id: Updated AWS Access Key ID.
            aws_secret_access_key: Updated AWS Secret Access Key (write-only).
            rate_limit_per_minute: Updated rate limit per minute.
            is_active: Updated active status flag.
            priority: Updated routing priority order.
            encrypted_credentials: Updated encrypted credentials mapping.
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            Dictionary representation of the updated provider configuration.

        Raises:
            NovaValidationError: If provider_id is missing or empty.
            NovaAPIError: If the server rejects the update payload.
        """
        if not provider_id or not str(provider_id).strip():
            raise NovaValidationError("provider_id must be a non-empty string.")
        clean_id = quote(str(provider_id).strip(), safe="")

        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name.strip()
        if provider_type is not None:
            payload["provider_type"] = str(provider_type).strip()

        if senders is not None:
            if not isinstance(senders, (list, tuple)):
                raise NovaValidationError(
                    "senders must be a list of sender dictionaries."
                )
            formatted_senders = []
            for idx, s in enumerate(senders):
                if not isinstance(s, Mapping):
                    raise NovaValidationError(
                        f"Each sender entry must be a dictionary, got {type(s).__name__} at index {idx}."
                    )
                if "email" not in s or not str(s["email"]).strip():
                    raise NovaValidationError(
                        f"Sender entry at index {idx} must contain a non-empty 'email' field."
                    )
                formatted_senders.append(dict(s))
            payload["senders"] = formatted_senders

        if smtp_host is not None:
            payload["smtp_host"] = str(smtp_host)
        if smtp_port is not None:
            payload["smtp_port"] = int(smtp_port)
        if tls_enabled is not None:
            payload["tls_enabled"] = bool(tls_enabled)
        if authentication_type is not None:
            payload["authentication_type"] = str(authentication_type)
        if smtp_user is not None:
            payload["smtp_user"] = str(smtp_user)
        if smtp_password is not None:
            payload["smtp_password"] = str(smtp_password)
        if aws_region is not None:
            payload["aws_region"] = str(aws_region)
        if aws_access_key_id is not None:
            payload["aws_access_key_id"] = str(aws_access_key_id)
        if aws_secret_access_key is not None:
            payload["aws_secret_access_key"] = str(aws_secret_access_key)
        if rate_limit_per_minute is not None:
            payload["rate_limit_per_minute"] = int(rate_limit_per_minute)
        if is_active is not None:
            payload["is_active"] = bool(is_active)
        if priority is not None:
            payload["priority"] = int(priority)
        if encrypted_credentials is not None:
            payload["encrypted_credentials"] = dict(encrypted_credentials)

        response = self._transport.request(
            "PATCH",
            f"providers/{clean_id}/",
            json=payload,
            tenant_id=tenant_id,
            allow_retry=False,
        )
        return parse_model(ProviderConfigurationCreateUpdate, response.data or {})

    def delete(
        self,
        provider_id: str,
        *,
        tenant_id: str | None = None,
    ) -> None:
        """Delete a provider configuration from the tenant workspace.

        Endpoint: DELETE /api/v1/providers/{id}/

        .. note::
            Provider deletion has external side effects and is never
            automatically retried by the SDK.

        Args:
            provider_id: Provider configuration UUID.
            tenant_id: Optional explicit tenant UUID override.

        Raises:
            NovaValidationError: If provider_id is missing or empty.
            NovaNotFoundError: If the provider configuration was not found.
        """
        if not provider_id or not str(provider_id).strip():
            raise NovaValidationError("provider_id must be a non-empty string.")
        clean_id = quote(str(provider_id).strip(), safe="")

        self._transport.request(
            "DELETE",
            f"providers/{clean_id}/",
            tenant_id=tenant_id,
            allow_retry=False,
        )

    def types(
        self,
        *,
        tenant_id: str | None = None,
    ) -> builtins.list[dict[str, Any]]:
        """List supported email provider integration types and metadata.

        Endpoint: GET /api/v1/providers/types/

        Args:
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            List of supported provider type specifications (key, label, description).
        """
        response = self._transport.request(
            "GET",
            "providers/types/",
            tenant_id=tenant_id,
        )
        if isinstance(response.data, list):
            return response.data
        return []

    def test(
        self,
        provider_id: str,
        *,
        recipient_email: str,
        tenant_id: str | None = None,
    ) -> ProviderTestDispatch:
        """Dispatch a real verification test email via the specified provider integration.

        Endpoint: POST /api/v1/providers/{id}/test/

        .. warning::
            This operation dispatches a real test email asynchronously via Celery
            to the given `recipient_email` using this provider integration.
            Side-effect operations are never automatically retried by the SDK.
            Unit tests must always use mocks and never invoke this against
            live production or sensitive recipient mailboxes.

        Args:
            provider_id: Provider configuration UUID (required).
            recipient_email: Destination recipient email address for test message (required).
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            Dictionary containing dispatch result:
            - `success`: Boolean confirmation flag.
            - `message`: Human-readable dispatch summary.
            - `message_id`: Created EmailMessage code (e.g. 'MSG001').
            - `task_id`: Celery background task UUID.

        Raises:
            NovaValidationError: If provider_id or recipient_email is missing or empty.
            NovaAPIError: If the server rejects the test email request.
        """
        if not provider_id or not str(provider_id).strip():
            raise NovaValidationError("provider_id must be a non-empty string.")
        if not recipient_email or not str(recipient_email).strip():
            raise NovaValidationError("recipient_email must be a non-empty string.")

        clean_id = quote(str(provider_id).strip(), safe="")
        clean_recipient = str(recipient_email).strip()

        payload = {
            "recipient_email": clean_recipient,
        }

        response = self._transport.request(
            "POST",
            f"providers/{clean_id}/test/",
            json=payload,
            tenant_id=tenant_id,
            allow_retry=False,
        )
        return parse_model(ProviderTestDispatch, response.data or {})
