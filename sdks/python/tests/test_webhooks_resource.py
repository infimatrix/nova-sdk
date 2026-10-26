"""Tests for WebhooksResource client."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from helpers import json_response

from nova_sdk import (
    NovaAuthenticationError,
    NovaNotFoundError,
    NovaPermissionError,
    NovaRateLimitError,
    NovaServerError,
    NovaValidationError,
    WebhookEvent,
    WebhooksResource,
)

VALID_WEBHOOK_ID = "99999999-9999-9999-9999-999999999999"
TENANT_ALPHA = "11111111-1111-1111-1111-111111111111"
TENANT_BETA = "22222222-2222-2222-2222-222222222222"


def test_webhooks_list_defaults(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/webhooks/"
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
                        "id": VALID_WEBHOOK_ID,
                        "name": "Production Events",
                        "url": "https://api.example.com/webhooks/prod",
                        "secret": "whsec_0123456789abcdef0123456789abcdef",
                        "secret_masked": "whsec_••••••••••••••••••••••••",
                        "events": [WebhookEvent.EMAIL_DELIVERED],
                        "is_active": True,
                    },
                    {
                        "id": "88888888-8888-8888-8888-888888888888",
                        "name": "Staging Webhook",
                        "url": "https://api.example.com/webhooks/stage",
                        "secret": "whsec_fedcba9876543210fedcba9876543210",
                        "secret_masked": "whsec_••••••••••••••••••••••••",
                        "events": [WebhookEvent.EMAIL_BOUNCED],
                        "is_active": False,
                    },
                ],
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    webhooks = client.webhooks.list()

    assert len(webhooks) == 2
    assert webhooks[0]["name"] == "Production Events"
    assert webhooks[1]["name"] == "Staging Webhook"
    assert webhooks.pagination.count == 2
    names = [w["name"] for w in webhooks]
    assert names == ["Production Events", "Staging Webhook"]


def test_webhooks_list_with_query_params(mock_client_factory):
    captured_params: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/webhooks/"
        captured_params.update(dict(request.url.params))
        return json_response(data={"results": [], "pagination": {"count": 0}})

    client = mock_client_factory(handler, api_key="nova_key_test")
    client.webhooks.list(
        search="example.com",
        ordering="-created_at",
        page=2,
        page_size=10,
        params={"is_active": "true"},
    )

    assert captured_params["search"] == "example.com"
    assert captured_params["ordering"] == "-created_at"
    assert captured_params["page"] == "2"
    assert captured_params["page_size"] == "10"
    assert captured_params["is_active"] == "true"


def test_webhooks_get_success(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == f"/api/v1/webhooks/{VALID_WEBHOOK_ID}/"
        return json_response(
            data={
                "id": VALID_WEBHOOK_ID,
                "name": "Email Events Webhook",
                "url": "https://api.example.com/webhooks/email-events",
                "secret": "whsec_0123456789abcdef0123456789abcdef",
                "secret_masked": "whsec_••••••••••••••••••••••••",
                "events": [
                    WebhookEvent.CONTACT_CREATED,
                    WebhookEvent.EMAIL_DELIVERED,
                ],
                "is_active": True,
                "created_at": "2026-10-24T12:00:00Z",
                "updated_at": "2026-10-24T12:00:00Z",
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    webhook = client.webhooks.get(VALID_WEBHOOK_ID)

    assert webhook["id"] == VALID_WEBHOOK_ID
    assert webhook["name"] == "Email Events Webhook"
    assert webhook["url"] == "https://api.example.com/webhooks/email-events"
    assert webhook["secret"] == "whsec_0123456789abcdef0123456789abcdef"
    assert webhook["secret_masked"] == "whsec_••••••••••••••••••••••••"
    assert len(webhook["events"]) == 2
    assert webhook["is_active"] is True


def test_webhooks_get_validation_error(mock_client_factory):
    client = mock_client_factory(lambda _: json_response())
    with pytest.raises(
        NovaValidationError, match="webhook_id must be a non-empty string"
    ):
        client.webhooks.get("")
    with pytest.raises(
        NovaValidationError, match="webhook_id must be a non-empty string"
    ):
        client.webhooks.get("   ")


def test_webhooks_create_success(mock_client_factory):
    captured_payload: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/webhooks/"
        nonlocal captured_payload
        captured_payload = json.loads(request.content.decode("utf-8"))
        return json_response(
            status_code=201,
            data={
                "id": VALID_WEBHOOK_ID,
                "name": captured_payload["name"],
                "url": captured_payload["url"],
                "secret": "whsec_newsecret1234567890abcdef1234",
                "secret_masked": "whsec_••••••••••••••••••••••••",
                "events": captured_payload.get("events", []),
                "is_active": captured_payload.get("is_active", True),
                "created_at": "2026-10-24T12:00:00Z",
                "updated_at": "2026-10-24T12:00:00Z",
            },
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    res = client.webhooks.create(
        name="CRM Delivery Listener",
        url="https://crm.example.com/nova-events",
        events=[WebhookEvent.EMAIL_DELIVERED, WebhookEvent.EMAIL_BOUNCED],
        is_active=True,
    )

    assert res["id"] == VALID_WEBHOOK_ID
    assert res["name"] == "CRM Delivery Listener"
    assert res["secret"] == "whsec_newsecret1234567890abcdef1234"
    assert captured_payload["name"] == "CRM Delivery Listener"
    assert captured_payload["url"] == "https://crm.example.com/nova-events"
    assert captured_payload["events"] == ["email.delivered", "email.bounced"]
    assert captured_payload["is_active"] is True


def test_webhooks_create_validation_errors(mock_client_factory):
    client = mock_client_factory(lambda _: json_response())

    with pytest.raises(NovaValidationError, match="name must be a non-empty string"):
        client.webhooks.create(name="", url="https://example.com")

    with pytest.raises(NovaValidationError, match="url must be a non-empty string"):
        client.webhooks.create(name="Valid Name", url="")

    with pytest.raises(
        NovaValidationError, match="events must be a sequence of event key strings"
    ):
        client.webhooks.create(
            name="Valid Name",
            url="https://example.com",
            events="not-a-sequence",  # type: ignore[arg-type]
        )


def test_webhooks_update_success(mock_client_factory):
    captured_payload: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == f"/api/v1/webhooks/{VALID_WEBHOOK_ID}/"
        nonlocal captured_payload
        captured_payload = json.loads(request.content.decode("utf-8"))
        return json_response(
            data={
                "id": VALID_WEBHOOK_ID,
                "name": captured_payload.get("name", "Original Name"),
                "url": captured_payload.get("url", "https://api.example.com"),
                "events": captured_payload.get(
                    "events", [WebhookEvent.EMAIL_DELIVERED]
                ),
                "is_active": captured_payload.get("is_active", True),
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    res = client.webhooks.update(
        VALID_WEBHOOK_ID,
        name="Updated Webhook",
        events=[WebhookEvent.EMAIL_OPENED, WebhookEvent.EMAIL_CLICKED],
        is_active=False,
    )

    assert res["name"] == "Updated Webhook"
    assert res["is_active"] is False
    assert captured_payload["name"] == "Updated Webhook"
    assert captured_payload["events"] == ["email.opened", "email.clicked"]
    assert captured_payload["is_active"] is False
    assert "url" not in captured_payload


def test_webhooks_update_validation(mock_client_factory):
    client = mock_client_factory(lambda _: json_response())

    with pytest.raises(
        NovaValidationError, match="webhook_id must be a non-empty string"
    ):
        client.webhooks.update("", name="Valid Name")

    with pytest.raises(
        NovaValidationError, match="events must be a sequence of event key strings"
    ):
        client.webhooks.update(VALID_WEBHOOK_ID, events="not-a-sequence")  # type: ignore[arg-type]


def test_webhooks_delete_success(mock_client_factory):
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == f"/api/v1/webhooks/{VALID_WEBHOOK_ID}/"
        nonlocal called
        called = True
        return httpx.Response(status_code=204)

    client = mock_client_factory(handler, api_key="nova_key_test")
    result = client.webhooks.delete(VALID_WEBHOOK_ID)

    assert called is True
    assert result is None


def test_webhooks_delete_validation(mock_client_factory):
    client = mock_client_factory(lambda _: json_response())
    with pytest.raises(
        NovaValidationError, match="webhook_id must be a non-empty string"
    ):
        client.webhooks.delete("   ")


def test_webhooks_events_enumeration(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/webhooks/events/"
        return json_response(
            data=[
                {"key": "contact.created", "label": "contact.created"},
                {"key": "email.delivered", "label": "email.delivered"},
                {"key": "email.bounced", "label": "email.bounced"},
            ]
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    event_list = client.webhooks.events()

    assert len(event_list) == 3
    keys = [e["key"] for e in event_list]
    assert "contact.created" in keys
    assert "email.delivered" in keys
    assert "email.bounced" in keys


def test_webhooks_rotate_secret(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == f"/api/v1/webhooks/{VALID_WEBHOOK_ID}/rotate-secret/"
        return json_response(
            data={
                "secret": "whsec_rotated999999999999999999999999",
                "message": "Webhook secret rotated successfully for 'Email Events Webhook'.",
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    res = client.webhooks.rotate_secret(VALID_WEBHOOK_ID)

    assert res["secret"] == "whsec_rotated999999999999999999999999"
    assert "rotated successfully" in res["message"]


def test_webhooks_rotate_secret_validation(mock_client_factory):
    client = mock_client_factory(lambda _: json_response())
    with pytest.raises(
        NovaValidationError, match="webhook_id must be a non-empty string"
    ):
        client.webhooks.rotate_secret("")


def test_webhooks_test_dispatch(mock_client_factory):
    captured_payload: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == f"/api/v1/webhooks/{VALID_WEBHOOK_ID}/send-test/"
        nonlocal captured_payload
        captured_payload = json.loads(request.content.decode("utf-8"))
        return json_response(
            data={
                "success": True,
                "message": f"Test webhook event '{captured_payload['event_type']}' dispatched successfully.",
                "webhook_id": VALID_WEBHOOK_ID,
                "task_id": "celery-webhook-task-uuid",
                "url": "https://api.example.com/webhooks/test",
                "event_type": captured_payload["event_type"],
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    res = client.webhooks.test(
        VALID_WEBHOOK_ID,
        event_type=WebhookEvent.EMAIL_OPENED,
    )

    assert res["success"] is True
    assert res["event_type"] == "email.opened"
    assert res["task_id"] == "celery-webhook-task-uuid"
    assert captured_payload["event_type"] == "email.opened"


def test_webhooks_test_validation_errors(mock_client_factory):
    client = mock_client_factory(lambda _: json_response())

    with pytest.raises(
        NovaValidationError, match="webhook_id must be a non-empty string"
    ):
        client.webhooks.test("", event_type=WebhookEvent.EMAIL_DELIVERED)

    with pytest.raises(
        NovaValidationError, match="event_type must be a non-empty string"
    ):
        client.webhooks.test(VALID_WEBHOOK_ID, event_type="")


def test_webhooks_tenant_isolation_and_override(mock_client_factory):
    captured_tenant_headers: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_tenant_headers.append(request.headers.get("X-Tenant-ID"))
        return json_response(data={"results": [], "pagination": {"count": 0}})

    client = mock_client_factory(
        handler,
        api_key="nova_key_test",
        tenant_id=TENANT_ALPHA,
    )

    # 1. Standard request uses client-configured tenant
    client.webhooks.list()
    assert captured_tenant_headers[-1] == TENANT_ALPHA

    # 2. Per-request override uses specified tenant
    client.webhooks.list(tenant_id=TENANT_BETA)
    assert captured_tenant_headers[-1] == TENANT_BETA

    # 3. Client configured tenant remains completely untouched
    assert client.tenant_id == TENANT_ALPHA


def test_webhooks_no_automatic_retries_on_side_effects(mock_client_factory):
    """Verify create, update, delete, rotate_secret, and test are NEVER retried on 500/503 errors."""
    call_counts = {
        "create": 0,
        "update": 0,
        "delete": 0,
        "rotate_secret": 0,
        "test": 0,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        method = request.method
        path = request.url.path

        if method == "POST" and path == "/api/v1/webhooks/":
            call_counts["create"] += 1
            return json_response(status_code=500, message="Server error on create")
        elif method == "PATCH":
            call_counts["update"] += 1
            return json_response(status_code=503, message="Unavailable on update")
        elif method == "DELETE":
            call_counts["delete"] += 1
            return json_response(status_code=500, message="Server error on delete")
        elif method == "POST" and "rotate-secret" in path:
            call_counts["rotate_secret"] += 1
            return json_response(status_code=500, message="Server error on rotate")
        elif method == "POST" and "send-test" in path:
            call_counts["test"] += 1
            return json_response(status_code=500, message="Server error on send-test")

        return json_response()

    client = mock_client_factory(handler, api_key="nova_key_test", max_retries=3)

    # create
    with pytest.raises(NovaServerError):
        client.webhooks.create(name="Failing Webhook", url="https://example.com")
    assert call_counts["create"] == 1

    # update
    with pytest.raises(NovaServerError):
        client.webhooks.update(VALID_WEBHOOK_ID, name="New Name")
    assert call_counts["update"] == 1

    # delete
    with pytest.raises(NovaServerError):
        client.webhooks.delete(VALID_WEBHOOK_ID)
    assert call_counts["delete"] == 1

    # rotate_secret
    with pytest.raises(NovaServerError):
        client.webhooks.rotate_secret(VALID_WEBHOOK_ID)
    assert call_counts["rotate_secret"] == 1

    # test
    with pytest.raises(NovaServerError):
        client.webhooks.test(VALID_WEBHOOK_ID)
    assert call_counts["test"] == 1


def test_webhooks_secret_redaction_in_exceptions(mock_client_factory):
    """Ensure raw secret keys are never exposed in exception strings or representations."""
    raw_secret = "whsec_confidential_hmac_secret_key_12345"

    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=400,
            message="Invalid webhook configuration.",
            data={"secret": [raw_secret]},
        )

    client = mock_client_factory(handler, api_key="nova_key_test")

    with pytest.raises(NovaValidationError) as exc_info:
        client.webhooks.rotate_secret(VALID_WEBHOOK_ID)

    err = exc_info.value
    err_str = str(err)
    err_repr = repr(err)

    # Raw secret must never be leaked into exception messages or representations
    assert raw_secret not in err_str
    assert raw_secret not in err_repr
    assert "Invalid webhook configuration" in err_str


def test_webhooks_typed_api_exceptions(mock_client_factory):
    status_map = [
        (400, NovaValidationError),
        (401, NovaAuthenticationError),
        (403, NovaPermissionError),
        (404, NovaNotFoundError),
        (429, NovaRateLimitError),
        (500, NovaServerError),
    ]

    for status_code, exc_class in status_map:

        def handler(request: httpx.Request, sc=status_code) -> httpx.Response:
            return json_response(status_code=sc, message=f"Error {sc}")

        client = mock_client_factory(handler, api_key="nova_key_test")
        with pytest.raises(exc_class):
            client.webhooks.get(VALID_WEBHOOK_ID)


def test_webhooks_registration_and_enum_constants():
    """Verify WebhooksResource is cleanly registered on NovaClient and WebhookEvent choices match backend."""
    from nova_sdk import NovaClient

    client = NovaClient(api_key="nova_key_test")
    assert isinstance(client.webhooks, WebhooksResource)

    # Verify all 20 WebhookEvent constants match backend WebhookEventChoices exactly
    assert WebhookEvent.CONTACT_CREATED == "contact.created"
    assert WebhookEvent.CONTACT_DELETED == "contact.deleted"
    assert WebhookEvent.CONTACT_UPDATED == "contact.updated"

    assert WebhookEvent.LIST_SUBSCRIBED == "list.subscribed"
    assert WebhookEvent.LIST_UNSUBSCRIBED == "list.unsubscribed"
    assert WebhookEvent.LIST_CONFIRMED == "list.confirmed"
    assert WebhookEvent.LIST_RESUBSCRIBED == "list.resubscribed"
    assert WebhookEvent.LIST_BOUNCED == "list.bounced"
    assert WebhookEvent.LIST_COMPLAINED == "list.complained"
    assert WebhookEvent.LIST_PENDING == "list.pending"
    assert WebhookEvent.LIST_REMOVED == "list.removed"

    assert WebhookEvent.SEGMENT_JOINED == "segment.joined"
    assert WebhookEvent.SEGMENT_LEFT == "segment.left"

    assert WebhookEvent.EMAIL_SENT == "email.sent"
    assert WebhookEvent.EMAIL_DELIVERED == "email.delivered"
    assert WebhookEvent.EMAIL_OPENED == "email.opened"
    assert WebhookEvent.EMAIL_CLICKED == "email.clicked"
    assert WebhookEvent.EMAIL_BOUNCED == "email.bounced"
    assert WebhookEvent.EMAIL_COMPLAINED == "email.complained"
    assert WebhookEvent.EMAIL_UNSUBSCRIBED == "email.unsubscribed"

    assert WebhookEvent.CUSTOM_EVENT_CREATED == "custom_event.created"
    assert WebhookEvent.CUSTOM_EVENT_UPDATED == "custom_event.updated"
    assert WebhookEvent.CUSTOM_EVENT_DELETED == "custom_event.deleted"

    client.close()
