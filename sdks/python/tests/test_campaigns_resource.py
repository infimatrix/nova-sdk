"""Tests for CampaignsResource and TransactionalNotificationsResource."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from helpers import json_response

from nova_sdk import (
    CampaignsResource,
    NovaAuthenticationError,
    NovaNotFoundError,
    NovaPermissionError,
    NovaRateLimitError,
    NovaServerError,
    NovaValidationError,
    TransactionalNotificationsResource,
)

VALID_NOTIFICATION_ID = "33333333-3333-3333-3333-333333333333"
VALID_TEMPLATE_ID = "44444444-4444-4444-4444-444444444444"
TENANT_ALPHA = "11111111-1111-1111-1111-111111111111"
TENANT_BETA = "22222222-2222-2222-2222-222222222222"


def test_transactional_list_defaults(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/campaigns/transactional/"
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
                        "id": VALID_NOTIFICATION_ID,
                        "display_id": "ID001",
                        "name": "Welcome Notification",
                        "api_identifier": "welcome_email",
                        "template_id": VALID_TEMPLATE_ID,
                        "template_name": "Welcome Template",
                        "description": "Triggered on signup",
                        "created_at": "2026-10-24T12:00:00Z",
                        "updated_at": "2026-10-24T12:00:00Z",
                    },
                    {
                        "id": "55555555-5555-5555-5555-555555555555",
                        "display_id": "ID002",
                        "name": "Password Reset",
                        "api_identifier": "password_reset",
                        "template_id": None,
                        "template_name": "",
                        "description": "Triggered on forgot password",
                        "created_at": "2026-10-24T12:05:00Z",
                        "updated_at": "2026-10-24T12:05:00Z",
                    },
                ],
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    notifications = client.campaigns.transactional.list()

    assert len(notifications) == 2
    assert notifications[0]["name"] == "Welcome Notification"
    assert notifications[0]["api_identifier"] == "welcome_email"
    assert notifications[0]["template_id"] == VALID_TEMPLATE_ID
    assert notifications[1]["name"] == "Password Reset"
    assert notifications.pagination.count == 2
    names = [n["name"] for n in notifications]
    assert names == ["Welcome Notification", "Password Reset"]


def test_transactional_list_with_query_params(mock_client_factory):
    captured_params: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/campaigns/transactional/"
        captured_params.update(dict(request.url.params))
        return json_response(data={"results": [], "pagination": {"count": 0}})

    client = mock_client_factory(handler, api_key="nova_key_test")
    client.campaigns.transactional.list(
        search="Welcome",
        ordering="-created_at",
        page=2,
        page_size=10,
        params={"custom_filter": "yes"},
    )

    assert captured_params["search"] == "Welcome"
    assert captured_params["ordering"] == "-created_at"
    assert captured_params["page"] == "2"
    assert captured_params["page_size"] == "10"
    assert captured_params["custom_filter"] == "yes"


def test_transactional_get_success(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert (
            request.url.path
            == f"/api/v1/campaigns/transactional/{VALID_NOTIFICATION_ID}/"
        )
        return json_response(
            data={
                "id": VALID_NOTIFICATION_ID,
                "display_id": "ID001",
                "name": "Order Confirmation",
                "api_identifier": "order_confirmation",
                "template_id": VALID_TEMPLATE_ID,
                "template_name": "Receipt Template",
                "description": "Triggered upon payment",
                "created_at": "2026-10-24T12:00:00Z",
                "updated_at": "2026-10-24T12:00:00Z",
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    notif = client.campaigns.transactional.get(VALID_NOTIFICATION_ID)

    assert notif["id"] == VALID_NOTIFICATION_ID
    assert notif["name"] == "Order Confirmation"
    assert notif["api_identifier"] == "order_confirmation"


def test_transactional_get_invalid_id():
    client = mock_client_factory_stub()
    with pytest.raises(
        NovaValidationError, match="notification_id must be a non-empty string"
    ):
        client.campaigns.transactional.get("")

    with pytest.raises(
        NovaValidationError, match="notification_id must be a non-empty string"
    ):
        client.campaigns.transactional.get("   ")


def test_transactional_create_success(mock_client_factory):
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_body
        assert request.method == "POST"
        assert request.url.path == "/api/v1/campaigns/transactional/"
        captured_body = json.loads(request.content.decode("utf-8"))
        return json_response(
            status_code=201,
            data={
                "id": VALID_NOTIFICATION_ID,
                "display_id": "ID003",
                "name": captured_body["name"],
                "api_identifier": captured_body["api_identifier"],
                "template_id": captured_body.get("template_id"),
                "template_name": "Welcome Template",
                "description": captured_body.get("description", ""),
                "created_at": "2026-10-24T12:00:00Z",
                "updated_at": "2026-10-24T12:00:00Z",
            },
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    created = client.campaigns.transactional.create(
        name="Security Alert",
        api_identifier="security_alert",
        template_id=VALID_TEMPLATE_ID,
        description="Triggered on suspicious login",
    )

    assert captured_body["name"] == "Security Alert"
    assert captured_body["api_identifier"] == "security_alert"
    assert captured_body["template_id"] == VALID_TEMPLATE_ID
    assert captured_body["description"] == "Triggered on suspicious login"
    assert created["id"] == VALID_NOTIFICATION_ID
    assert created["display_id"] == "ID003"


def test_transactional_create_minimal(mock_client_factory):
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_body
        assert request.method == "POST"
        assert request.url.path == "/api/v1/campaigns/transactional/"
        captured_body = json.loads(request.content.decode("utf-8"))
        return json_response(
            status_code=201,
            data={
                "id": VALID_NOTIFICATION_ID,
                "display_id": "ID004",
                "name": captured_body["name"],
                "api_identifier": captured_body["api_identifier"],
                "template_id": None,
                "template_name": "",
                "description": "",
                "created_at": "2026-10-24T12:00:00Z",
                "updated_at": "2026-10-24T12:00:00Z",
            },
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    created = client.campaigns.transactional.create(
        name="Simple Alert",
        api_identifier="simple_alert",
    )

    assert captured_body == {
        "name": "Simple Alert",
        "api_identifier": "simple_alert",
    }
    assert created["name"] == "Simple Alert"


def test_transactional_create_validation():
    client = mock_client_factory_stub()

    with pytest.raises(NovaValidationError, match="name must be a non-empty string"):
        client.campaigns.transactional.create(name="", api_identifier="valid_slug")

    with pytest.raises(NovaValidationError, match="name must be a non-empty string"):
        client.campaigns.transactional.create(name="   ", api_identifier="valid_slug")

    with pytest.raises(
        NovaValidationError, match="api_identifier must be a non-empty string"
    ):
        client.campaigns.transactional.create(name="Valid Name", api_identifier="")

    with pytest.raises(
        NovaValidationError, match="api_identifier must be a non-empty string"
    ):
        client.campaigns.transactional.create(name="Valid Name", api_identifier="   ")


def test_transactional_update_success(mock_client_factory):
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_body
        assert request.method == "PATCH"
        assert (
            request.url.path
            == f"/api/v1/campaigns/transactional/{VALID_NOTIFICATION_ID}/"
        )
        captured_body = json.loads(request.content.decode("utf-8"))
        return json_response(
            data={
                "id": VALID_NOTIFICATION_ID,
                "display_id": "ID001",
                "name": captured_body.get("name", "Original Name"),
                "api_identifier": captured_body.get("api_identifier", "original_slug"),
                "template_id": captured_body.get("template_id"),
                "template_name": "Updated Template",
                "description": captured_body.get("description", "Original description"),
                "created_at": "2026-10-24T12:00:00Z",
                "updated_at": "2026-10-24T12:10:00Z",
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    updated = client.campaigns.transactional.update(
        VALID_NOTIFICATION_ID,
        name="Updated Name",
        description="Updated description",
    )

    assert captured_body == {
        "name": "Updated Name",
        "description": "Updated description",
    }
    assert updated["name"] == "Updated Name"


def test_transactional_update_validation():
    client = mock_client_factory_stub()

    with pytest.raises(
        NovaValidationError, match="notification_id must be a non-empty string"
    ):
        client.campaigns.transactional.update("", name="New Name")

    with pytest.raises(
        NovaValidationError, match="At least one field must be provided to update"
    ):
        client.campaigns.transactional.update(VALID_NOTIFICATION_ID)

    with pytest.raises(NovaValidationError, match="name must be a non-empty string"):
        client.campaigns.transactional.update(VALID_NOTIFICATION_ID, name="   ")

    with pytest.raises(
        NovaValidationError, match="api_identifier must be a non-empty string"
    ):
        client.campaigns.transactional.update(
            VALID_NOTIFICATION_ID, api_identifier="   "
        )


def test_transactional_delete_success(mock_client_factory):
    delete_called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal delete_called
        assert request.method == "DELETE"
        assert (
            request.url.path
            == f"/api/v1/campaigns/transactional/{VALID_NOTIFICATION_ID}/"
        )
        delete_called = True
        return httpx.Response(status_code=204)

    client = mock_client_factory(handler, api_key="nova_key_test")
    result = client.campaigns.transactional.delete(VALID_NOTIFICATION_ID)

    assert delete_called is True
    assert result is None


def test_transactional_delete_invalid_id():
    client = mock_client_factory_stub()

    with pytest.raises(
        NovaValidationError, match="notification_id must be a non-empty string"
    ):
        client.campaigns.transactional.delete("")


def test_transactional_send_test_success(mock_client_factory):
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_body
        assert request.method == "POST"
        assert (
            request.url.path
            == f"/api/v1/campaigns/transactional/{VALID_NOTIFICATION_ID}/send-test/"
        )
        captured_body = json.loads(request.content.decode("utf-8"))
        return json_response(
            data={
                "message": (
                    f"Test email queued for dispatch to {captured_body['recipient_email']}."
                ),
                "message_id": "MSG042",
                "email_id": "66666666-6666-6666-6666-666666666666",
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    resp = client.campaigns.transactional.send_test(
        VALID_NOTIFICATION_ID,
        recipient_email="test.recipient@example.com",
        from_name="Nova Alerts",
        sender_email="alerts@novamail.io",
        provider_id="77777777-7777-7777-7777-777777777777",
        cc_emails="cc@example.com",
        bcc_emails="bcc@example.com",
        reply_to="support@novamail.io",
    )

    assert captured_body["recipient_email"] == "test.recipient@example.com"
    assert captured_body["from_name"] == "Nova Alerts"
    assert captured_body["sender_email"] == "alerts@novamail.io"
    assert captured_body["provider_id"] == "77777777-7777-7777-7777-777777777777"
    assert captured_body["cc_emails"] == "cc@example.com"
    assert captured_body["bcc_emails"] == "bcc@example.com"
    assert captured_body["reply_to"] == "support@novamail.io"
    assert "queued" in resp["message"]
    assert resp["message_id"] == "MSG042"
    assert resp["email_id"] == "66666666-6666-6666-6666-666666666666"


def test_transactional_send_test_minimal(mock_client_factory):
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_body
        assert request.method == "POST"
        assert (
            request.url.path
            == f"/api/v1/campaigns/transactional/{VALID_NOTIFICATION_ID}/send-test/"
        )
        captured_body = json.loads(request.content.decode("utf-8"))
        return json_response(
            data={
                "message": "Test email queued for dispatch.",
                "message_id": "MSG001",
                "email_id": "66666666-6666-6666-6666-666666666666",
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    client.campaigns.transactional.send_test(
        VALID_NOTIFICATION_ID,
        recipient_email="simple@example.com",
    )

    assert captured_body == {"recipient_email": "simple@example.com"}


def test_transactional_send_test_validation():
    client = mock_client_factory_stub()

    with pytest.raises(
        NovaValidationError, match="notification_id must be a non-empty string"
    ):
        client.campaigns.transactional.send_test("", recipient_email="user@example.com")

    with pytest.raises(
        NovaValidationError,
        match="recipient_email must be a valid non-empty email address",
    ):
        client.campaigns.transactional.send_test(
            VALID_NOTIFICATION_ID, recipient_email=""
        )

    with pytest.raises(
        NovaValidationError,
        match="recipient_email must be a valid non-empty email address",
    ):
        client.campaigns.transactional.send_test(
            VALID_NOTIFICATION_ID, recipient_email="not-an-email"
        )

    with pytest.raises(
        NovaValidationError,
        match="sender_email must be a valid email address",
    ):
        client.campaigns.transactional.send_test(
            VALID_NOTIFICATION_ID,
            recipient_email="user@example.com",
            sender_email="invalid-sender",
        )


def test_campaigns_top_level_shortcuts(mock_client_factory):
    """Verify client.campaigns top-level methods delegate to client.campaigns.transactional."""
    actions_called: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        method = request.method
        path = request.url.path

        if method == "GET" and path == "/api/v1/campaigns/transactional/":
            actions_called.append("list")
            return json_response(data={"results": [], "pagination": {"count": 0}})
        elif (
            method == "GET"
            and path == f"/api/v1/campaigns/transactional/{VALID_NOTIFICATION_ID}/"
        ):
            actions_called.append("get")
            return json_response(
                data={"id": VALID_NOTIFICATION_ID, "name": "Shortcut Notif"}
            )
        elif method == "POST" and path == "/api/v1/campaigns/transactional/":
            actions_called.append("create")
            return json_response(
                status_code=201,
                data={"id": VALID_NOTIFICATION_ID, "name": "Created Notif"},
            )
        elif method == "PATCH":
            actions_called.append("update")
            return json_response(
                data={"id": VALID_NOTIFICATION_ID, "name": "Updated Notif"}
            )
        elif method == "DELETE":
            actions_called.append("delete")
            return httpx.Response(status_code=204)
        elif method == "POST" and "send-test" in path:
            actions_called.append("send_test")
            return json_response(data={"message": "Queued", "message_id": "MSG1"})

        return json_response()

    client = mock_client_factory(handler, api_key="nova_key_test")

    client.campaigns.list()
    assert "list" in actions_called

    client.campaigns.get(VALID_NOTIFICATION_ID)
    assert "get" in actions_called

    client.campaigns.create(name="Top Level", api_identifier="top_level")
    assert "create" in actions_called

    client.campaigns.update(VALID_NOTIFICATION_ID, name="Top Level Updated")
    assert "update" in actions_called

    client.campaigns.delete(VALID_NOTIFICATION_ID)
    assert "delete" in actions_called

    client.campaigns.send_test(
        VALID_NOTIFICATION_ID, recipient_email="shortcut@example.com"
    )
    assert "send_test" in actions_called


def test_campaigns_no_automatic_retries_on_side_effects(mock_client_factory):
    """Verify create, update, delete, and send_test are NEVER automatically retried on 500/503 errors."""
    call_counts = {
        "create": 0,
        "update": 0,
        "delete": 0,
        "send_test": 0,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        method = request.method
        path = request.url.path

        if method == "POST" and path == "/api/v1/campaigns/transactional/":
            call_counts["create"] += 1
            return json_response(status_code=500, message="Server error on create")
        elif method == "PATCH":
            call_counts["update"] += 1
            return json_response(status_code=503, message="Unavailable on update")
        elif method == "DELETE":
            call_counts["delete"] += 1
            return json_response(status_code=500, message="Server error on delete")
        elif method == "POST" and "send-test" in path:
            call_counts["send_test"] += 1
            return json_response(status_code=500, message="Server error on send-test")

        return json_response()

    client = mock_client_factory(handler, api_key="nova_key_test", max_retries=3)

    # create
    with pytest.raises(NovaServerError):
        client.campaigns.transactional.create(
            name="Failing Notif", api_identifier="fail_slug"
        )
    assert call_counts["create"] == 1

    # update
    with pytest.raises(NovaServerError):
        client.campaigns.transactional.update(VALID_NOTIFICATION_ID, name="New Name")
    assert call_counts["update"] == 1

    # delete
    with pytest.raises(NovaServerError):
        client.campaigns.transactional.delete(VALID_NOTIFICATION_ID)
    assert call_counts["delete"] == 1

    # send_test
    with pytest.raises(NovaServerError):
        client.campaigns.transactional.send_test(
            VALID_NOTIFICATION_ID, recipient_email="fail@example.com"
        )
    assert call_counts["send_test"] == 1


def test_campaigns_safe_retries_on_read_operations(mock_client_factory):
    """Verify list and get succeed after bounded retries on transient errors."""
    attempts = {"list": 0, "get": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        method = request.method
        path = request.url.path

        if method == "GET" and path == "/api/v1/campaigns/transactional/":
            attempts["list"] += 1
            if attempts["list"] < 3:
                return json_response(status_code=503, message="Unavailable")
            return json_response(data={"results": [], "pagination": {"count": 0}})
        elif (
            method == "GET"
            and path == f"/api/v1/campaigns/transactional/{VALID_NOTIFICATION_ID}/"
        ):
            attempts["get"] += 1
            if attempts["get"] < 2:
                return json_response(status_code=502, message="Bad gateway")
            return json_response(
                data={"id": VALID_NOTIFICATION_ID, "name": "Recovered Notif"}
            )

        return json_response()

    client = mock_client_factory(
        handler,
        api_key="nova_key_test",
        max_retries=3,
        retry_backoff_factor=0.01,
        retry_jitter=False,
    )

    notifications = client.campaigns.transactional.list()
    assert len(notifications) == 0
    assert attempts["list"] == 3

    notif = client.campaigns.transactional.get(VALID_NOTIFICATION_ID)
    assert notif["name"] == "Recovered Notif"
    assert attempts["get"] == 2


def test_campaigns_tenant_context_and_overrides(mock_client_factory):
    """Verify X-Tenant-ID header forwarding and non-mutating per-request tenant override."""
    captured_tenant_headers: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_tenant_headers.append(request.headers.get("X-Tenant-ID"))
        return json_response(data={"results": [], "pagination": {"count": 0}})

    client = mock_client_factory(
        handler,
        api_key="nova_key_test",
        tenant_id=TENANT_ALPHA,
    )

    # 1. Standard call uses client-configured tenant
    client.campaigns.transactional.list()
    assert captured_tenant_headers[-1] == TENANT_ALPHA

    # 2. Per-request override uses specified tenant
    client.campaigns.transactional.list(tenant_id=TENANT_BETA)
    assert captured_tenant_headers[-1] == TENANT_BETA

    # 3. Client configured tenant remains completely untouched
    assert client.tenant_id == TENANT_ALPHA


def test_campaigns_api_error_propagation(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        if "not-found" in request.url.path:
            return json_response(
                status_code=404,
                message="Transactional notification not found.",
                error_code="not_found",
            )
        if "forbidden" in request.url.path:
            return json_response(
                status_code=403,
                message="Not a tenant member.",
                error_code="permission_denied",
            )
        if "unauthorized" in request.url.path:
            return json_response(
                status_code=401,
                message="Invalid authentication credentials.",
                error_code="authentication_failed",
            )
        if "rate-limit" in request.url.path:
            return json_response(
                status_code=429,
                message="Rate limit exceeded.",
                error_code="throttled",
            )
        return json_response()

    client = mock_client_factory(handler, api_key="nova_key_test")

    with pytest.raises(NovaNotFoundError, match="not found"):
        client.campaigns.transactional.get("not-found")

    with pytest.raises(NovaPermissionError, match="Not a tenant member"):
        client.campaigns.transactional.get("forbidden")

    with pytest.raises(NovaAuthenticationError, match="Invalid authentication"):
        client.campaigns.transactional.get("unauthorized")

    with pytest.raises(NovaRateLimitError, match="Rate limit exceeded"):
        client.campaigns.transactional.get("rate-limit")


def test_campaigns_exports_and_types():
    import nova_sdk

    assert hasattr(nova_sdk, "CampaignsResource")
    assert hasattr(nova_sdk, "TransactionalNotificationsResource")
    assert nova_sdk.CampaignsResource is CampaignsResource
    assert (
        nova_sdk.TransactionalNotificationsResource
        is TransactionalNotificationsResource
    )


# Helper stub factory for client-side validation tests with no HTTP calls
def mock_client_factory_stub():
    from nova_sdk.client import NovaClient

    return NovaClient(api_key="nova_key_test")
