"""Tests for AccessLogsResource and AuditResource."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

import httpx
import pytest
from helpers import json_response

from nova_sdk import (
    AccessLogCategory,
    AccessLogsResource,
    AuditResource,
    NovaNotFoundError,
    NovaPermissionError,
    NovaServerError,
    NovaValidationError,
)

VALID_LOG_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
VALID_USER_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
TENANT_ALPHA = "11111111-1111-1111-1111-111111111111"
TENANT_BETA = "22222222-2222-2222-2222-222222222222"


def test_access_logs_list_defaults(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/audit/access-logs/"
        assert request.headers.get("X-Tenant-ID") == TENANT_ALPHA
        assert not request.url.params
        return json_response(
            data={
                "pagination": {
                    "count": 2,
                    "page": 1,
                    "total_pages": 1,
                    "page_size": 20,
                },
                "results": [
                    {
                        "id": VALID_LOG_ID,
                        "tenant_id": TENANT_ALPHA,
                        "user_id": VALID_USER_ID,
                        "user_email": "user@example.com",
                        "category": "API_CALL",
                        "action": "list_contacts",
                        "http_method": "GET",
                        "path": "/api/v1/contacts/",
                        "status_code": 200,
                        "ip_address": "127.0.0.1",
                        "user_agent": "Mozilla/5.0",
                        "response_time_ms": 42.5,
                        "resource_type": "contact",
                        "resource_id": None,
                        "details": {},
                        "created_at": "2026-10-24T12:00:00Z",
                    },
                    {
                        "id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
                        "tenant_id": TENANT_ALPHA,
                        "user_id": None,
                        "user_email": "anonymous@example.com",
                        "category": "AUTH",
                        "action": "login",
                        "http_method": "POST",
                        "path": "/api/v1/auth/login/",
                        "status_code": 200,
                        "ip_address": "192.168.1.1",
                        "user_agent": "curl/7.68.0",
                        "response_time_ms": 120.0,
                        "resource_type": "user",
                        "resource_id": None,
                        "details": {},
                        "created_at": "2026-10-24T12:05:00Z",
                    },
                ],
            }
        )

    client = mock_client_factory(
        handler, api_key="nova_key_test", tenant_id=TENANT_ALPHA
    )
    logs = client.audit.access_logs.list()
    assert len(logs) == 2
    assert logs[0]["id"] == VALID_LOG_ID
    assert logs[0]["category"] == "API_CALL"
    assert logs.pagination is not None
    assert logs.pagination.count == 2
    assert logs.pagination.page == 1
    assert logs.pagination.page_size == 20


def test_access_logs_list_filters(mock_client_factory):
    captured_params: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/audit/access-logs/"
        captured_params.update(dict(request.url.params))
        return json_response(
            data={
                "pagination": {
                    "count": 1,
                    "page": 1,
                    "total_pages": 1,
                    "page_size": 10,
                },
                "results": [{"id": VALID_LOG_ID}],
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")

    # Test all filters, including status_code=0 preservation, date/datetime formatting, enum conversion
    after_dt = datetime(2026, 10, 1, 10, 0, 0, tzinfo=timezone.utc)
    before_d = date(2026, 10, 24)

    logs = client.audit.access_logs.list(
        category=AccessLogCategory.AUTH,
        user=VALID_USER_ID,
        user_email="admin@example.com",
        action="login_attempt",
        http_method="POST",
        status_code=0,  # Must preserve valid 0!
        status_code_gte=200,
        status_code_lte=500,
        resource_type="template",
        resource_id="rrrrrrrr-rrrr-rrrr-rrrr-rrrrrrrrrrrr",
        ip_address="10.0.0.1",
        created_after=after_dt,
        created_before=before_d,
        search="failed",
        ordering="-created_at",
        page=2,
        page_size=10,
        params={"extra_param": "custom_val"},
    )

    assert len(logs) == 1
    assert captured_params["category"] == "AUTH"
    assert captured_params["user"] == VALID_USER_ID
    assert captured_params["user_email"] == "admin@example.com"
    assert captured_params["action"] == "login_attempt"
    assert captured_params["http_method"] == "POST"
    assert captured_params["status_code"] == "0"
    assert captured_params["status_code_gte"] == "200"
    assert captured_params["status_code_lte"] == "500"
    assert captured_params["resource_type"] == "template"
    assert captured_params["resource_id"] == "rrrrrrrr-rrrr-rrrr-rrrr-rrrrrrrrrrrr"
    assert captured_params["ip_address"] == "10.0.0.1"
    assert captured_params["created_after"] == "2026-10-01T10:00:00+00:00"
    assert captured_params["created_before"] == "2026-10-24"
    assert captured_params["search"] == "failed"
    assert captured_params["ordering"] == "-created_at"
    assert captured_params["page"] == "2"
    assert captured_params["page_size"] == "10"
    assert captured_params["extra_param"] == "custom_val"


def test_access_logs_list_user_id_alias(mock_client_factory):
    captured_params: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_params.update(dict(request.url.params))
        return json_response(data={"pagination": {"count": 0}, "results": []})

    client = mock_client_factory(handler, api_key="nova_key_test")
    client.audit.access_logs.list(user_id=VALID_USER_ID)
    assert captured_params["user"] == VALID_USER_ID


def test_access_logs_get_success(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == f"/api/v1/audit/access-logs/{VALID_LOG_ID}/"
        assert request.headers.get("X-Tenant-ID") == TENANT_ALPHA
        return json_response(
            data={
                "id": VALID_LOG_ID,
                "tenant_id": TENANT_ALPHA,
                "user_id": VALID_USER_ID,
                "user_email": "admin@example.com",
                "category": "API_CALL",
                "action": "get_template",
                "http_method": "GET",
                "path": "/api/v1/templates/123/",
                "query_string": "preview=true",
                "status_code": 200,
                "ip_address": "127.0.0.1",
                "user_agent": "python-requests/2.28",
                "response_time_ms": 35.2,
                "resource_type": "template",
                "resource_id": "123",
                "details": {"cached": True},
                "created_at": "2026-10-24T12:00:00Z",
            }
        )

    client = mock_client_factory(
        handler, api_key="nova_key_test", tenant_id=TENANT_ALPHA
    )
    log = client.audit.access_logs.get(VALID_LOG_ID)
    assert log["id"] == VALID_LOG_ID
    assert log["action"] == "get_template"
    assert log["response_time_ms"] == 35.2
    assert log["query_string"] == "preview=true"


def test_access_logs_get_blank_id_validation():
    from nova_sdk.client import NovaClient

    client = NovaClient(api_key="nova_key_test")
    with pytest.raises(NovaValidationError, match="log_id must be a non-empty string"):
        client.audit.access_logs.get("")

    with pytest.raises(NovaValidationError, match="log_id must be a non-empty string"):
        client.audit.access_logs.get("   ")


def test_access_logs_get_not_found(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=404,
            message="Access log not found.",
            error_code="not_found",
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    with pytest.raises(NovaNotFoundError, match="Access log not found"):
        client.audit.access_logs.get(VALID_LOG_ID)


def test_access_logs_stats_success(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/audit/access-logs/stats/"
        assert request.headers.get("X-Tenant-ID") == TENANT_ALPHA
        return json_response(
            data={
                "total": 1250,
                "last_24h": 140,
                "last_7d": 850,
                "category_breakdown": {
                    "API_CALL": 800,
                    "AUTH": 300,
                    "CREATE": 100,
                    "DELETE": 50,
                },
                "top_users": [
                    {
                        "user__id": VALID_USER_ID,
                        "user__email": "admin@example.com",
                        "count": 450,
                    }
                ],
                "avg_response_time_ms": 48.75,
            }
        )

    client = mock_client_factory(
        handler, api_key="nova_key_test", tenant_id=TENANT_ALPHA
    )
    stats = client.audit.access_logs.stats()
    assert stats["total"] == 1250
    assert stats["last_24h"] == 140
    assert stats["last_7d"] == 850
    assert stats["category_breakdown"]["API_CALL"] == 800
    assert len(stats["top_users"]) == 1
    assert stats["top_users"][0]["user__email"] == "admin@example.com"
    assert stats["avg_response_time_ms"] == 48.75


def test_access_logs_stats_permission_denied(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=403,
            message="Only tenant administrators can view audit statistics.",
            error_code="permission_denied",
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    with pytest.raises(NovaPermissionError, match="tenant administrators"):
        client.audit.access_logs.stats()


def test_access_logs_stats_missing_tenant_context(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("X-Tenant-ID") is None
        return json_response(
            status_code=400,
            message="Tenant context is required for this operation.",
            error_code="tenant_required",
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    with pytest.raises(NovaValidationError, match="Tenant context is required"):
        client.audit.access_logs.stats()


def test_access_logs_safe_retries_on_read(mock_client_factory):
    """Verify list, get, and stats retry on bounded transient errors."""
    attempts = {"list": 0, "get": 0, "stats": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        method = request.method
        path = request.url.path

        if method == "GET" and path == "/api/v1/audit/access-logs/":
            attempts["list"] += 1
            if attempts["list"] < 3:
                return json_response(status_code=503, message="Unavailable")
            return json_response(
                data={"results": [{"id": VALID_LOG_ID}], "pagination": {"count": 1}}
            )

        if method == "GET" and path == f"/api/v1/audit/access-logs/{VALID_LOG_ID}/":
            attempts["get"] += 1
            if attempts["get"] < 2:
                return json_response(status_code=502, message="Bad gateway")
            return json_response(data={"id": VALID_LOG_ID, "action": "recovered"})

        if method == "GET" and path == "/api/v1/audit/access-logs/stats/":
            attempts["stats"] += 1
            if attempts["stats"] < 2:
                return json_response(status_code=504, message="Gateway timeout")
            return json_response(data={"total": 100})

        return json_response()

    client = mock_client_factory(
        handler,
        api_key="nova_key_test",
        max_retries=3,
        retry_backoff_factor=0.01,
        retry_jitter=False,
    )

    logs = client.audit.access_logs.list()
    assert len(logs) == 1
    assert attempts["list"] == 3

    log = client.audit.access_logs.get(VALID_LOG_ID)
    assert log["action"] == "recovered"
    assert attempts["get"] == 2

    stats = client.audit.access_logs.stats()
    assert stats["total"] == 100
    assert attempts["stats"] == 2


def test_access_logs_tenant_context_and_override(mock_client_factory):
    captured_tenant_headers: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_tenant_headers.append(request.headers.get("X-Tenant-ID"))
        if "/stats/" in request.url.path:
            return json_response(data={"total": 0})
        if request.url.path.endswith(f"/{VALID_LOG_ID}/"):
            return json_response(data={"id": VALID_LOG_ID})
        return json_response(data={"results": [], "pagination": {"count": 0}})

    client = mock_client_factory(
        handler,
        api_key="nova_key_test",
        tenant_id=TENANT_ALPHA,
    )

    # List default vs override
    client.audit.access_logs.list()
    assert captured_tenant_headers[-1] == TENANT_ALPHA

    client.audit.access_logs.list(tenant_id=TENANT_BETA)
    assert captured_tenant_headers[-1] == TENANT_BETA

    # Get default vs override
    client.audit.access_logs.get(VALID_LOG_ID)
    assert captured_tenant_headers[-1] == TENANT_ALPHA

    client.audit.access_logs.get(VALID_LOG_ID, tenant_id=TENANT_BETA)
    assert captured_tenant_headers[-1] == TENANT_BETA

    # Stats default vs override
    client.audit.access_logs.stats()
    assert captured_tenant_headers[-1] == TENANT_ALPHA

    client.audit.access_logs.stats(tenant_id=TENANT_BETA)
    assert captured_tenant_headers[-1] == TENANT_BETA

    # Client config remains untouched
    assert client.tenant_id == TENANT_ALPHA


def test_audit_top_level_shortcuts(mock_client_factory):
    actions_called: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/api/v1/audit/access-logs/":
            actions_called.append("list")
            return json_response(
                data={"results": [{"id": VALID_LOG_ID}], "pagination": {"count": 1}}
            )
        elif path == f"/api/v1/audit/access-logs/{VALID_LOG_ID}/":
            actions_called.append("get")
            return json_response(data={"id": VALID_LOG_ID})
        elif path == "/api/v1/audit/access-logs/stats/":
            actions_called.append("stats")
            return json_response(data={"total": 42})
        return json_response()

    client = mock_client_factory(handler, api_key="nova_key_test")

    # Call shortcuts directly on client.audit
    res_list = client.audit.list()
    assert len(res_list) == 1
    assert "list" in actions_called

    res_get = client.audit.get(VALID_LOG_ID)
    assert res_get["id"] == VALID_LOG_ID
    assert "get" in actions_called

    res_stats = client.audit.stats()
    assert res_stats["total"] == 42
    assert "stats" in actions_called


def test_audit_exports_and_enum():
    import nova_sdk

    assert hasattr(nova_sdk, "AccessLogCategory")
    assert hasattr(nova_sdk, "AccessLogsResource")
    assert hasattr(nova_sdk, "AuditResource")

    assert nova_sdk.AccessLogsResource is AccessLogsResource
    assert nova_sdk.AuditResource is AuditResource
    assert nova_sdk.AccessLogCategory is AccessLogCategory

    # Verify all 10 backend choices
    expected_categories = {
        "AUTH",
        "CREATE",
        "READ",
        "UPDATE",
        "DELETE",
        "UPLOAD",
        "DOWNLOAD",
        "EXPORT",
        "API_CALL",
        "SYSTEM",
    }
    actual_categories = {c.value for c in AccessLogCategory}
    assert actual_categories == expected_categories


def test_access_logs_raw_string_category_and_date_strings(mock_client_factory):
    captured_params: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_params.update(dict(request.url.params))
        return json_response(data={"pagination": {"count": 0}, "results": []})

    client = mock_client_factory(handler, api_key="nova_key_test")
    client.audit.access_logs.list(
        category="EXPORT",
        created_after="2026-10-01T00:00:00Z",
        created_before="2026-10-15T23:59:59Z",
    )
    assert captured_params["category"] == "EXPORT"
    assert captured_params["created_after"] == "2026-10-01T00:00:00Z"
    assert captured_params["created_before"] == "2026-10-15T23:59:59Z"


def test_access_logs_stats_docstring_mentions_admin_role():
    doc = AccessLogsResource.stats.__doc__
    assert doc is not None
    assert "IsTenantAdmin" in doc or "admin" in doc.lower()


def test_access_logs_500_server_error_propagation(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=500,
            message="Internal database connection failure.",
            error_code="internal_error",
        )

    client = mock_client_factory(handler, api_key="nova_key_test", max_retries=0)
    with pytest.raises(NovaServerError, match="Internal database connection failure"):
        client.audit.access_logs.list()
