"""Tenants and Tenant Memberships resource client for Nova SDK."""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from nova_sdk._model_base import parse_model
from nova_sdk.exceptions import NovaValidationError
from nova_sdk.models import PaginatedResponse
from nova_sdk.resources.base import BaseResource
from nova_sdk.schemas import (
    Membership,
    MembershipCreate,
    MembershipUpdate,
    Tenant,
    TenantCreate,
    TenantUpdate,
)

if TYPE_CHECKING:
    from nova_sdk.client import NovaClient
    from nova_sdk.http import HTTPTransport


class TenantMembershipsResource(BaseResource):
    """Resource client for managing tenant membership bindings."""

    def __init__(
        self,
        transport: HTTPTransport,
        client: NovaClient | None = None,
    ) -> None:
        super().__init__(transport)
        self._client = client

    def _resolve_tenant_id(self, tenant_id: str | None) -> str:
        tid = tenant_id or self._transport.config.tenant_id
        if not tid or not str(tid).strip():
            raise NovaValidationError(
                "tenant_id must be provided or configured on the client."
            )
        try:
            return str(uuid.UUID(str(tid).strip()))
        except (ValueError, AttributeError) as exc:
            raise NovaValidationError(f"Invalid UUID for tenant_id: {tid!r}") from exc

    def list(
        self,
        tenant_id: str | None = None,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> PaginatedResponse[Membership]:
        """List member users associated with a specific tenant organization.

        Endpoint: GET /api/v1/tenants/{tenant_id}/members/
        Requires Tenant Admin or Platform Admin privileges.
        """
        tid = self._resolve_tenant_id(tenant_id)
        response = self._transport.request(
            "GET",
            f"tenants/{tid}/members/",
            params=params,
        )
        return PaginatedResponse.from_response(
            response, item_parser=Membership.from_dict
        )

    def add(
        self,
        tenant_id: str | None = None,
        *,
        email: str,
        role: str = "VIEWER",
        status: str = "ACTIVE",
    ) -> MembershipCreate:
        """Add a registered user to a tenant organization.

        Endpoint: POST /api/v1/tenants/{tenant_id}/members/
        Requires Tenant Admin or Platform Admin privileges.

        Args:
            tenant_id: Target tenant UUID string (or client default if omitted).
            email: Registered account email of the user to add.
            role: Assigned tenant role ('TENANT_ADMIN', 'TEMPLATE_MANAGER', 'CAMPAIGN_MANAGER', 'SENDER', 'VIEWER').
            status: Membership status ('ACTIVE', 'INACTIVE').
        """
        tid = self._resolve_tenant_id(tenant_id)
        if not email or not isinstance(email, str) or not email.strip():
            raise NovaValidationError("email must be a non-empty string.")

        payload: dict[str, Any] = {
            "email": email.strip(),
            "role": role,
            "status": status,
        }
        response = self._transport.request(
            "POST",
            f"tenants/{tid}/members/",
            json=payload,
        )
        return parse_model(MembershipCreate, response.data or {})

    def get(
        self,
        membership_id: str,
        *,
        tenant_id: str | None = None,
    ) -> Membership:
        """Retrieve a specific tenant membership binding.

        Endpoint: GET /api/v1/tenants/{tenant_id}/members/{membership_id}/
        Requires Tenant Admin or Platform Admin privileges.
        """
        tid = self._resolve_tenant_id(tenant_id)
        if not membership_id or not str(membership_id).strip():
            raise NovaValidationError("membership_id must be a non-empty string.")
        try:
            valid_mid = str(uuid.UUID(str(membership_id).strip()))
        except (ValueError, AttributeError) as exc:
            raise NovaValidationError(
                f"Invalid UUID for membership_id: {membership_id!r}"
            ) from exc

        response = self._transport.request(
            "GET",
            f"tenants/{tid}/members/{valid_mid}/",
        )
        return parse_model(Membership, response.data or {})

    def update(
        self,
        membership_id: str,
        *,
        tenant_id: str | None = None,
        role: str | None = None,
        status: str | None = None,
    ) -> MembershipUpdate:
        """Update a tenant member's role or membership status.

        Endpoint: PATCH /api/v1/tenants/{tenant_id}/members/{membership_id}/
        Requires Tenant Admin or Platform Admin privileges.
        """
        tid = self._resolve_tenant_id(tenant_id)
        if not membership_id or not str(membership_id).strip():
            raise NovaValidationError("membership_id must be a non-empty string.")
        try:
            valid_mid = str(uuid.UUID(str(membership_id).strip()))
        except (ValueError, AttributeError) as exc:
            raise NovaValidationError(
                f"Invalid UUID for membership_id: {membership_id!r}"
            ) from exc

        payload: dict[str, Any] = {}
        if role is not None:
            payload["role"] = role
        if status is not None:
            payload["status"] = status

        response = self._transport.request(
            "PATCH",
            f"tenants/{tid}/members/{valid_mid}/",
            json=payload,
        )
        return parse_model(MembershipUpdate, response.data or {})

    def remove(
        self,
        membership_id: str,
        *,
        tenant_id: str | None = None,
    ) -> None:
        """Remove a user from a tenant organization.

        Endpoint: DELETE /api/v1/tenants/{tenant_id}/members/{membership_id}/
        Requires Tenant Admin or Platform Admin privileges.
        """
        tid = self._resolve_tenant_id(tenant_id)
        if not membership_id or not str(membership_id).strip():
            raise NovaValidationError("membership_id must be a non-empty string.")
        try:
            valid_mid = str(uuid.UUID(str(membership_id).strip()))
        except (ValueError, AttributeError) as exc:
            raise NovaValidationError(
                f"Invalid UUID for membership_id: {membership_id!r}"
            ) from exc

        self._transport.request(
            "DELETE",
            f"tenants/{tid}/members/{valid_mid}/",
        )

    # Alias delete to remove
    delete = remove


class TenantsResource(BaseResource):
    """Resource client for Tenant workspace management and member bindings."""

    def __init__(
        self,
        transport: HTTPTransport,
        client: NovaClient | None = None,
    ) -> None:
        super().__init__(transport)
        self._client = client
        self.memberships = TenantMembershipsResource(transport, client)

    def _resolve_tenant_id(self, tenant_id: str | None) -> str:
        tid = tenant_id or self._transport.config.tenant_id
        if not tid or not str(tid).strip():
            raise NovaValidationError(
                "tenant_id must be provided or configured on the client."
            )
        try:
            return str(uuid.UUID(str(tid).strip()))
        except (ValueError, AttributeError) as exc:
            raise NovaValidationError(f"Invalid UUID for tenant_id: {tid!r}") from exc

    def list(
        self,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> PaginatedResponse[Tenant]:
        """List active tenant organizations accessible to the authenticated user.

        Endpoint: GET /api/v1/tenants/
        """
        response = self._transport.request("GET", "tenants/", params=params)
        return PaginatedResponse.from_response(response, item_parser=Tenant.from_dict)

    def create(
        self,
        *,
        name: str,
        slug: str,
        website: str | None = None,
        logo_url: str | None = None,
        status: str = "ACTIVE",
    ) -> TenantCreate:
        """Create a new tenant organization boundary.

        Endpoint: POST /api/v1/tenants/

        Args:
            name: Human-readable workspace name.
            slug: URL-safe unique tenant slug.
            website: Optional organization domain URL.
            logo_url: Optional organization logo URL.
            status: Initial tenant status ('ACTIVE', 'INACTIVE', 'SUSPENDED').
        """
        if not name or not isinstance(name, str) or not name.strip():
            raise NovaValidationError("name must be a non-empty string.")
        if not slug or not isinstance(slug, str) or not slug.strip():
            raise NovaValidationError("slug must be a non-empty string.")

        payload: dict[str, Any] = {
            "name": name.strip(),
            "slug": slug.strip().lower(),
            "status": status,
        }
        if website is not None:
            payload["website"] = website.strip()
        if logo_url is not None:
            payload["logo_url"] = logo_url.strip()

        response = self._transport.request("POST", "tenants/", json=payload)
        return parse_model(TenantCreate, response.data or {})

    def get(self, tenant_id: str | None = None) -> Tenant:
        """Retrieve details for a specific tenant workspace.

        Endpoint: GET /api/v1/tenants/{tenant_id}/
        Requires membership in the tenant organization.
        """
        tid = self._resolve_tenant_id(tenant_id)
        response = self._transport.request("GET", f"tenants/{tid}/")
        return parse_model(Tenant, response.data or {})

    def update(
        self,
        tenant_id: str | None = None,
        *,
        name: str | None = None,
        website: str | None = None,
        logo_url: str | None = None,
        status: str | None = None,
    ) -> TenantUpdate:
        """Update tenant workspace attributes.

        Endpoint: PATCH /api/v1/tenants/{tenant_id}/
        Requires Tenant Admin or Platform Admin privileges.
        """
        tid = self._resolve_tenant_id(tenant_id)

        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name.strip()
        if website is not None:
            payload["website"] = website.strip()
        if logo_url is not None:
            payload["logo_url"] = logo_url.strip()
        if status is not None:
            payload["status"] = status

        response = self._transport.request("PATCH", f"tenants/{tid}/", json=payload)
        return parse_model(TenantUpdate, response.data or {})

    def delete(self, tenant_id: str | None = None) -> None:
        """Hard delete a tenant workspace and all associated resources.

        Endpoint: DELETE /api/v1/tenants/{tenant_id}/
        Requires Tenant Admin or Platform Admin privileges.
        """
        tid = self._resolve_tenant_id(tenant_id)
        self._transport.request("DELETE", f"tenants/{tid}/")

    # Member shortcut conveniences forwarding to memberships sub-resource
    def list_members(
        self,
        tenant_id: str | None = None,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> PaginatedResponse[Membership]:
        """Shortcut for client.tenants.memberships.list()."""
        return self.memberships.list(tenant_id=tenant_id, params=params)

    def add_member(
        self,
        tenant_id: str | None = None,
        *,
        email: str,
        role: str = "VIEWER",
        status: str = "ACTIVE",
    ) -> MembershipCreate:
        """Shortcut for client.tenants.memberships.add()."""
        return self.memberships.add(
            tenant_id=tenant_id, email=email, role=role, status=status
        )

    def get_member(
        self,
        membership_id: str,
        *,
        tenant_id: str | None = None,
    ) -> Membership:
        """Shortcut for client.tenants.memberships.get()."""
        return self.memberships.get(membership_id=membership_id, tenant_id=tenant_id)

    def update_member(
        self,
        membership_id: str,
        *,
        tenant_id: str | None = None,
        role: str | None = None,
        status: str | None = None,
    ) -> MembershipUpdate:
        """Shortcut for client.tenants.memberships.update()."""
        return self.memberships.update(
            membership_id=membership_id,
            tenant_id=tenant_id,
            role=role,
            status=status,
        )

    def remove_member(
        self,
        membership_id: str,
        *,
        tenant_id: str | None = None,
    ) -> None:
        """Shortcut for client.tenants.memberships.remove()."""
        self.memberships.remove(membership_id=membership_id, tenant_id=tenant_id)
