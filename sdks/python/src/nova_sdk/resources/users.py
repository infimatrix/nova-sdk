"""Users resource client for Nova SDK."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from nova_sdk._model_base import parse_model
from nova_sdk.models import PaginatedResponse
from nova_sdk.resources.base import BaseResource
from nova_sdk.schemas import User, UserMe


class UsersResource(BaseResource):
    """Resource client for user profiles within the active tenant."""

    def list(
        self,
        *,
        page: int | None = None,
        page_size: int | None = None,
        params: Mapping[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[User]:
        """List users.

        Endpoint: GET /api/v1/users/

        Args:
            page: Specific page number.
            page_size: Number of records per page.
            params: Additional raw query parameters.
            tenant_id: Optional explicit tenant UUID override.
        """
        query_params: dict[str, Any] = dict(params or {})
        if page is not None:
            query_params["page"] = page
        if page_size is not None:
            query_params["page_size"] = page_size

        response = self._transport.request(
            "GET",
            "users/",
            params=query_params or None,
            tenant_id=tenant_id,
            allow_retry=True,
        )
        return PaginatedResponse.from_response(response, item_parser=User.from_dict)

    def me(self, *, tenant_id: str | None = None) -> UserMe:
        """Retrieve the authenticated user's profile and tenant context.

        Endpoint: GET /api/v1/users/me/
        """
        response = self._transport.request(
            "GET", "users/me/", tenant_id=tenant_id, allow_retry=True
        )
        return parse_model(UserMe, response.data or {})
