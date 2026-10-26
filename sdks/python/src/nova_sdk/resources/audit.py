"""Audit and Access Logs resource clients for Nova SDK."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from nova_sdk._model_base import parse_model
from nova_sdk.exceptions import NovaValidationError
from nova_sdk.models import AccessLogCategory, PaginatedResponse
from nova_sdk.resources.base import BaseResource
from nova_sdk.schemas import AccessLog, AccessLogStats, AccessLogSummary

if TYPE_CHECKING:
    from nova_sdk.client import NovaClient
    from nova_sdk.http import HTTPTransport


class AccessLogsResource(BaseResource):
    """Resource client for querying tenant access audit logs and activity statistics."""

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
        category: str | AccessLogCategory | None = None,
        user: str | None = None,
        user_id: str | None = None,
        user_email: str | None = None,
        action: str | None = None,
        http_method: str | None = None,
        status_code: int | None = None,
        status_code_gte: int | None = None,
        status_code_lte: int | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        created_after: str | datetime | date | None = None,
        created_before: str | datetime | date | None = None,
        search: str | None = None,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        params: Mapping[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[AccessLogSummary]:
        """List access audit logs for the active or specified tenant.

        Endpoint: GET /api/v1/audit/access-logs/
        Permissions: IsAuthenticated, IsTenantMember

        Args:
            category: Activity category filter (e.g. 'AUTH', 'CREATE', 'API_CALL' or AccessLogCategory enum).
            user: Filter by user UUID string (maps to backend 'user' query parameter).
            user_id: Alias for 'user' parameter.
            user_email: Case-insensitive partial match on user email.
            action: Case-insensitive partial match on action label (e.g. 'User Login').
            http_method: Exact match on HTTP request method (e.g. 'GET', 'POST').
            status_code: Exact match on HTTP response status code (e.g. 200, 400).
            status_code_gte: Filter logs with response status code >= value.
            status_code_lte: Filter logs with response status code <= value.
            resource_type: Case-insensitive partial match on affected resource (e.g. 'Contact', 'Template').
            resource_id: Exact match on resource primary key.
            ip_address: Exact match on client IP address.
            created_after: Return logs created at or after this timestamp (ISO 8601 string, date, or datetime).
            created_before: Return logs created at or before this timestamp (ISO 8601 string, date, or datetime).
            search: Full-text search across action, path, user email, resource_type, and description.
            ordering: Sort field (e.g. 'created_at', 'status_code', 'response_time_ms', 'action'; prefix with '-' for desc).
            page: Specific page number (default: 1).
            page_size: Number of records per page (default: 20).
            params: Additional raw query parameters.
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            PaginatedResponse of access log summary records.
        """
        query_params: dict[str, Any] = dict(params or {})

        if category is not None:
            query_params["category"] = (
                category.value if hasattr(category, "value") else str(category).strip()
            )
        if user is not None:
            query_params["user"] = str(user).strip()
        elif user_id is not None:
            query_params["user"] = str(user_id).strip()

        if user_email is not None:
            query_params["user_email"] = str(user_email).strip()
        if action is not None:
            query_params["action"] = str(action).strip()
        if http_method is not None:
            query_params["http_method"] = str(http_method).strip().upper()

        if status_code is not None:
            query_params["status_code"] = int(status_code)
        if status_code_gte is not None:
            query_params["status_code_gte"] = int(status_code_gte)
        if status_code_lte is not None:
            query_params["status_code_lte"] = int(status_code_lte)

        if resource_type is not None:
            query_params["resource_type"] = str(resource_type).strip()
        if resource_id is not None:
            query_params["resource_id"] = str(resource_id).strip()
        if ip_address is not None:
            query_params["ip_address"] = str(ip_address).strip()

        if created_after is not None:
            if isinstance(created_after, (datetime, date)):
                query_params["created_after"] = created_after.isoformat()
            else:
                query_params["created_after"] = str(created_after).strip()

        if created_before is not None:
            if isinstance(created_before, (datetime, date)):
                query_params["created_before"] = created_before.isoformat()
            else:
                query_params["created_before"] = str(created_before).strip()

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
            "audit/access-logs/",
            params=query_params or None,
            tenant_id=tenant_id,
            allow_retry=True,
        )
        return PaginatedResponse.from_response(
            response, item_parser=AccessLogSummary.from_dict
        )

    def get(
        self,
        log_id: str,
        *,
        tenant_id: str | None = None,
    ) -> AccessLog:
        """Retrieve full details of a specific access log entry.

        Endpoint: GET /api/v1/audit/access-logs/{id}/
        Permissions: IsAuthenticated, IsTenantMember

        Args:
            log_id: Access log UUID.
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            Dictionary matching the detailed AccessLogSerializer representation.

        Raises:
            NovaValidationError: If log_id is missing or empty.
            NovaNotFoundError: If the access log record does not exist.
        """
        if not log_id or not str(log_id).strip():
            raise NovaValidationError("log_id must be a non-empty string.")
        clean_id = quote(str(log_id).strip(), safe="")

        response = self._transport.request(
            "GET",
            f"audit/access-logs/{clean_id}/",
            tenant_id=tenant_id,
            allow_retry=True,
        )
        return parse_model(AccessLog, response.data)

    def stats(
        self,
        *,
        tenant_id: str | None = None,
    ) -> AccessLogStats:
        """Retrieve aggregated access log and activity statistics for the tenant.

        Endpoint: GET /api/v1/audit/access-logs/stats/
        Permissions: IsAuthenticated, IsTenantAdmin

        Note:
            Requires TENANT_ADMIN role. Regular tenant members will receive
            a NovaPermissionError (HTTP 403).

        Args:
            tenant_id: Optional explicit tenant UUID override.

        Returns:
            Dictionary containing aggregated tenant statistics:
            - total (int): All-time total access log count.
            - last_24h (int): Number of access logs recorded in the past 24 hours.
            - last_7d (int): Number of access logs recorded in the past 7 days.
            - category_breakdown (dict[str, int]): Count of logs per AccessLogCategory.
            - top_users (list[dict]): Top active users by activity count in the past 7 days.
            - avg_response_time_ms (float | None): Average response time in milliseconds.

        Raises:
            NovaPermissionError: If the authenticated user is not a Tenant Admin (403).
            NovaValidationError: If tenant context is missing (400).
        """
        response = self._transport.request(
            "GET",
            "audit/access-logs/stats/",
            tenant_id=tenant_id,
            allow_retry=True,
        )
        return parse_model(AccessLogStats, response.data or {})


class AuditResource(BaseResource):
    """Resource client for Nova audit and compliance logging.

    Provides access to access audit logs via the `.access_logs` sub-resource,
    as well as convenient top-level shortcuts.
    """

    def __init__(
        self,
        transport: HTTPTransport,
        client: NovaClient | None = None,
    ) -> None:
        super().__init__(transport)
        self._client = client
        self.access_logs = AccessLogsResource(transport, client)

    def list(
        self,
        *,
        category: str | AccessLogCategory | None = None,
        user: str | None = None,
        user_id: str | None = None,
        user_email: str | None = None,
        action: str | None = None,
        http_method: str | None = None,
        status_code: int | None = None,
        status_code_gte: int | None = None,
        status_code_lte: int | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        ip_address: str | None = None,
        created_after: str | datetime | date | None = None,
        created_before: str | datetime | date | None = None,
        search: str | None = None,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        params: Mapping[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> PaginatedResponse[AccessLogSummary]:
        """List access audit logs (shortcut to .access_logs.list)."""
        return self.access_logs.list(
            category=category,
            user=user,
            user_id=user_id,
            user_email=user_email,
            action=action,
            http_method=http_method,
            status_code=status_code,
            status_code_gte=status_code_gte,
            status_code_lte=status_code_lte,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            created_after=created_after,
            created_before=created_before,
            search=search,
            ordering=ordering,
            page=page,
            page_size=page_size,
            params=params,
            tenant_id=tenant_id,
        )

    def get(
        self,
        log_id: str,
        *,
        tenant_id: str | None = None,
    ) -> AccessLog:
        """Retrieve full details of an access log entry (shortcut to .access_logs.get)."""
        return self.access_logs.get(log_id, tenant_id=tenant_id)

    def stats(
        self,
        *,
        tenant_id: str | None = None,
    ) -> AccessLogStats:
        """Retrieve access log statistics (shortcut to .access_logs.stats)."""
        return self.access_logs.stats(tenant_id=tenant_id)
