"""Tests for EmailsResource client."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from helpers import json_response

from nova_sdk.exceptions import (
    NovaAuthenticationError,
    NovaNotFoundError,
    NovaPermissionError,
    NovaRateLimitError,
    NovaServerError,
    NovaTimeoutError,
    NovaValidationError,
)
from nova_sdk.models import EmailMessageStatus

TENANT_ALPHA = "11111111-1111-1111-1111-111111111111"
TENANT_BETA = "22222222-2222-2222-2222-222222222222"
VALID_TEMPLATE_ID = "33333333-3333-3333-3333-333333333333"
VALID_GROUP_ID = "44444444-4444-4444-4444-444444444444"
VALID_CONTACT_ID = "55555555-5555-5555-5555-555555555555"
VALID_EMAIL_LOG_ID = "66666666-6666-6666-6666-666666666666"


# ==============================================================================
# Email Dispatch: send()
# ==============================================================================


def test_send_email_success(mock_client_factory):
    captured_request: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/emails/logs/send/"
        assert request.headers.get("X-Tenant-ID") == TENANT_ALPHA
        captured_request["body"] = json.loads(request.content.decode("utf-8"))
        return json_response(
            status_code=201,
            data={
                "id": VALID_EMAIL_LOG_ID,
                "message_id": "MSG001",
                "sender_name": "Nova Dispatcher",
                "sender_email": "notifications@example.com",
                "receiver_name": "Alice Smith",
                "receiver_email": "alice@example.com",
                "template_name": "Welcome",
                "subject": "Welcome to Nova!",
                "note": "Initial onboarding",
                "status": EmailMessageStatus.PROCESSING,
                "created_at": "2026-10-24T12:00:00Z",
            },
        )

    client = mock_client_factory(
        handler, api_key="nova_key_test", tenant_id=TENANT_ALPHA
    )
    result = client.emails.send(
        recipient_email="alice@example.com",
        subject="Welcome to Nova!",
        recipient_name="Alice Smith",
        sender_name="Nova Dispatcher",
        sender_email="notifications@example.com",
        html_content="<h1>Welcome Alice</h1>",
        text_content="Welcome Alice",
        template_id=VALID_TEMPLATE_ID,
        template_name="Welcome",
        note="Initial onboarding",
    )

    assert result["message_id"] == "MSG001"
    assert result["receiver_email"] == "alice@example.com"
    assert result["status"] == EmailMessageStatus.PROCESSING
    assert captured_request["body"]["recipient_email"] == "alice@example.com"
    assert captured_request["body"]["subject"] == "Welcome to Nova!"
    assert captured_request["body"]["template_id"] == VALID_TEMPLATE_ID


def test_send_email_minimal_and_tenant_override(mock_client_factory):
    captured_request: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.headers.get("X-Tenant-ID") == TENANT_BETA
        captured_request["body"] = json.loads(request.content.decode("utf-8"))
        return json_response(
            status_code=201,
            data={
                "id": VALID_EMAIL_LOG_ID,
                "message_id": "MSG002",
                "receiver_email": "bob@example.com",
                "subject": "Minimal subject",
                "status": EmailMessageStatus.PROCESSING,
            },
        )

    client = mock_client_factory(
        handler, api_key="nova_key_test", tenant_id=TENANT_ALPHA
    )
    result = client.emails.send(
        recipient_email="bob@example.com",
        subject="Minimal subject",
        tenant_id=TENANT_BETA,
    )

    assert result["message_id"] == "MSG002"
    assert captured_request["body"] == {
        "recipient_email": "bob@example.com",
        "subject": "Minimal subject",
    }
    # Verify client tenant_id was not permanently changed
    assert client.tenant_id == TENANT_ALPHA


def test_send_email_input_validation(mock_client_factory):
    client = mock_client_factory(lambda r: json_response(), api_key="nova_key_test")

    with pytest.raises(
        NovaValidationError, match="recipient_email must be a non-empty string"
    ):
        client.emails.send(recipient_email="", subject="Hello")

    with pytest.raises(NovaValidationError, match="subject must be a non-empty string"):
        client.emails.send(recipient_email="test@example.com", subject="   ")


def test_send_email_no_retries_on_500(mock_client_factory):
    """Critical safety test: POST send operations MUST NOT be retried."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return json_response(
            status_code=500,
            message="Internal Server Error during email dispatch",
        )

    client = mock_client_factory(handler, api_key="nova_key_test", max_retries=3)

    with pytest.raises(NovaServerError, match="Internal Server Error"):
        client.emails.send(recipient_email="test@example.com", subject="Test")

    # MUST be exactly 1 call — NO retries!
    assert call_count == 1


def test_send_email_no_retries_on_503(mock_client_factory):
    """Critical safety test: POST send operations MUST NOT be retried even on 503."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return json_response(status_code=503, message="Mail server unavailable")

    client = mock_client_factory(handler, api_key="nova_key_test", max_retries=3)

    with pytest.raises(NovaServerError):
        client.emails.send(recipient_email="test@example.com", subject="Test")

    assert call_count == 1


def test_send_email_no_retries_on_timeout(mock_client_factory):
    """Critical safety test: Timeout during email send must NOT trigger retry."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        raise httpx.ReadTimeout("Socket timeout while dispatching email")

    client = mock_client_factory(handler, api_key="nova_key_test", max_retries=3)

    with pytest.raises(NovaTimeoutError):
        client.emails.send(recipient_email="test@example.com", subject="Test")

    assert call_count == 1


# ==============================================================================
# Batch Dispatch: bulk_send()
# ==============================================================================


def test_bulk_send_success(mock_client_factory):
    captured_request: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/emails/logs/bulk-send/"
        captured_request["body"] = json.loads(request.content.decode("utf-8"))
        return json_response(
            status_code=200,
            data={"message": "Queued 2 emails for dispatch.", "count": 2},
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    result = client.emails.bulk_send(
        template_id=VALID_TEMPLATE_ID,
        contact_ids=[VALID_CONTACT_ID, "77777777-7777-7777-7777-777777777777"],
        sender_email="marketing@company.com",
        fallback_variables={"first_name": "Valued Customer"},
    )

    assert result["count"] == 2
    assert "Queued" in result["message"]
    assert captured_request["body"]["template_id"] == VALID_TEMPLATE_ID
    assert len(captured_request["body"]["contact_ids"]) == 2
    assert captured_request["body"]["sender_email"] == "marketing@company.com"
    assert captured_request["body"]["fallback_variables"] == {
        "first_name": "Valued Customer"
    }


def test_bulk_send_validation(mock_client_factory):
    client = mock_client_factory(lambda r: json_response(), api_key="nova_key_test")

    with pytest.raises(
        NovaValidationError, match="template_id must be a non-empty string"
    ):
        client.emails.bulk_send(
            template_id="",
            contact_ids=[VALID_CONTACT_ID],
            sender_email="sender@example.com",
        )

    with pytest.raises(
        NovaValidationError, match="contact_ids must be a non-empty list"
    ):
        client.emails.bulk_send(
            template_id=VALID_TEMPLATE_ID,
            contact_ids=[],
            sender_email="sender@example.com",
        )

    with pytest.raises(
        NovaValidationError, match="contact_ids cannot exceed 1000 contacts"
    ):
        oversized_list = [f"id-{i}" for i in range(1001)]
        client.emails.bulk_send(
            template_id=VALID_TEMPLATE_ID,
            contact_ids=oversized_list,
            sender_email="sender@example.com",
        )

    with pytest.raises(
        NovaValidationError, match="sender_email must be a non-empty string"
    ):
        client.emails.bulk_send(
            template_id=VALID_TEMPLATE_ID,
            contact_ids=[VALID_CONTACT_ID],
            sender_email="",
        )

    with pytest.raises(
        NovaValidationError, match="fallback_variables must be a mapping"
    ):
        client.emails.bulk_send(
            template_id=VALID_TEMPLATE_ID,
            contact_ids=[VALID_CONTACT_ID],
            sender_email="sender@example.com",
            fallback_variables="invalid",  # type: ignore
        )


def test_bulk_send_no_retries(mock_client_factory):
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return json_response(status_code=500, message="Database timeout")

    client = mock_client_factory(handler, api_key="nova_key_test", max_retries=3)

    with pytest.raises(NovaServerError):
        client.emails.bulk_send(
            template_id=VALID_TEMPLATE_ID,
            contact_ids=[VALID_CONTACT_ID],
            sender_email="sender@example.com",
        )

    assert call_count == 1


# ==============================================================================
# Group Dispatch: group_send()
# ==============================================================================


def test_group_send_success(mock_client_factory):
    captured_request: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/emails/logs/group-send/"
        captured_request["body"] = json.loads(request.content.decode("utf-8"))
        return json_response(
            status_code=200,
            data={"message": "Queued 50 emails for dispatch.", "count": 50},
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    result = client.emails.group_send(
        template_id=VALID_TEMPLATE_ID,
        group_id=VALID_GROUP_ID,
        sender_email="news@company.com",
        fallback_variables={"newsletter_issue": "42"},
    )

    assert result["count"] == 50
    assert captured_request["body"]["template_id"] == VALID_TEMPLATE_ID
    assert captured_request["body"]["group_id"] == VALID_GROUP_ID
    assert captured_request["body"]["sender_email"] == "news@company.com"


def test_group_send_validation(mock_client_factory):
    client = mock_client_factory(lambda r: json_response(), api_key="nova_key_test")

    with pytest.raises(
        NovaValidationError, match="template_id must be a non-empty string"
    ):
        client.emails.group_send(
            template_id="",
            group_id=VALID_GROUP_ID,
            sender_email="sender@example.com",
        )

    with pytest.raises(
        NovaValidationError, match="group_id must be a non-empty string"
    ):
        client.emails.group_send(
            template_id=VALID_TEMPLATE_ID,
            group_id="   ",
            sender_email="sender@example.com",
        )

    with pytest.raises(
        NovaValidationError, match="sender_email must be a non-empty string"
    ):
        client.emails.group_send(
            template_id=VALID_TEMPLATE_ID,
            group_id=VALID_GROUP_ID,
            sender_email="",
        )


def test_group_send_no_retries(mock_client_factory):
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return json_response(status_code=502, message="Bad Gateway")

    client = mock_client_factory(handler, api_key="nova_key_test", max_retries=3)

    with pytest.raises(NovaServerError):
        client.emails.group_send(
            template_id=VALID_TEMPLATE_ID,
            group_id=VALID_GROUP_ID,
            sender_email="sender@example.com",
        )

    assert call_count == 1


# ==============================================================================
# Email Logs: list_logs(), get_log(), preview()
# ==============================================================================


def test_list_logs_defaults(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/emails/logs/"
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
                        "id": VALID_EMAIL_LOG_ID,
                        "message_id": "MSG001",
                        "sender_name": "Nova",
                        "receiver_email": "user1@example.com",
                        "subject": "Hello 1",
                        "status": EmailMessageStatus.DELIVERED,
                    },
                    {
                        "id": "77777777-7777-7777-7777-777777777777",
                        "message_id": "MSG002",
                        "sender_name": "Nova",
                        "receiver_email": "user2@example.com",
                        "subject": "Hello 2",
                        "status": EmailMessageStatus.FAILED,
                    },
                ],
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    logs = client.emails.list_logs()

    assert len(logs) == 2
    assert logs[0]["message_id"] == "MSG001"
    assert logs[0]["status"] == EmailMessageStatus.DELIVERED
    assert logs[1]["status"] == EmailMessageStatus.FAILED
    assert logs.pagination.count == 2


def test_list_logs_with_filters(mock_client_factory):
    captured_params: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/emails/logs/"
        captured_params.update(dict(request.url.params))
        return json_response(data={"results": [], "pagination": {"count": 0}})

    client = mock_client_factory(handler, api_key="nova_key_test")
    client.emails.list_logs(
        status=EmailMessageStatus.DELIVERED,
        search="john",
        ordering="-created_at",
        page=2,
        page_size=10,
    )

    assert captured_params["status"] == EmailMessageStatus.DELIVERED
    assert captured_params["search"] == "john"
    assert captured_params["ordering"] == "-created_at"
    assert captured_params["page"] == "2"
    assert captured_params["page_size"] == "10"


def test_get_log_detail(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == f"/api/v1/emails/logs/{VALID_EMAIL_LOG_ID}/"
        return json_response(
            data={
                "id": VALID_EMAIL_LOG_ID,
                "message_id": "MSG001",
                "receiver_email": "alice@example.com",
                "subject": "Detailed email",
                "html_content": "<p>Content</p>",
                "text_content": "Content",
                "metadata": {"template_id": VALID_TEMPLATE_ID},
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    detail = client.emails.get_log(VALID_EMAIL_LOG_ID)

    assert detail["id"] == VALID_EMAIL_LOG_ID
    assert detail["html_content"] == "<p>Content</p>"


def test_get_log_validation_and_404(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(status_code=404, message="Email log not found")

    client = mock_client_factory(handler, api_key="nova_key_test")

    with pytest.raises(
        NovaValidationError, match="email_log_id must be a non-empty string"
    ):
        client.emails.get_log("")

    with pytest.raises(NovaNotFoundError, match="Email log not found"):
        client.emails.get_log("non-existent-id")


def test_preview(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == f"/api/v1/emails/logs/{VALID_EMAIL_LOG_ID}/preview/"
        return json_response(
            data={
                "id": VALID_EMAIL_LOG_ID,
                "message_id": "MSG001",
                "subject": "Rendered Subject",
                "html_content": "<div class='rendered'>Hello</div>",
                "text_content": "Hello",
                "metadata": {"tags": ["welcome"]},
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    preview_data = client.emails.preview(VALID_EMAIL_LOG_ID)

    assert preview_data["subject"] == "Rendered Subject"
    assert preview_data["html_content"] == "<div class='rendered'>Hello</div>"


def test_preview_validation(mock_client_factory):
    client = mock_client_factory(lambda r: json_response(), api_key="nova_key_test")
    with pytest.raises(
        NovaValidationError, match="email_log_id must be a non-empty string"
    ):
        client.emails.preview("  ")


# ==============================================================================
# CSV Export: export_csv()
# ==============================================================================


def test_export_csv_as_text(mock_client_factory):
    csv_body = (
        "Message ID,Sender Name,Sender Email,Receiver Name,Receiver Email,Template Name,Subject,Note,Status,Created At\r\n"
        "MSG001,Acme,noreply@acme.com,Jane,jane@example.com,Welcome,Welcome!,Delivered,DELIVERED,2026-10-24 10:00:00\r\n"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/emails/logs/export/"
        assert request.url.params.get("status") == "DELIVERED"
        return httpx.Response(
            status_code=200,
            headers={
                "Content-Type": "text/csv",
                "Content-Disposition": 'attachment; filename="email_logs.csv"',
            },
            content=csv_body.encode("utf-8"),
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    result = client.emails.export_csv(status="DELIVERED")

    assert isinstance(result, str)
    assert "Message ID,Sender Name,Sender Email" in result
    assert "MSG001,Acme,noreply@acme.com" in result


def test_export_csv_as_bytes(mock_client_factory):
    csv_bytes = b"Message ID,Status\r\nMSG001,DELIVERED\r\n"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            headers={"Content-Type": "text/csv"},
            content=csv_bytes,
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    result = client.emails.export_csv(as_bytes=True)

    assert isinstance(result, bytes)
    assert result == csv_bytes


def test_export_csv_empty_response(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            headers={"Content-Type": "text/csv"},
            content=b"",
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    text_result = client.emails.export_csv()
    assert text_result == ""

    bytes_result = client.emails.export_csv(as_bytes=True)
    assert bytes_result == b""


def test_export_csv_error_handling(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=403, message="Permission denied to export logs."
        )

    client = mock_client_factory(handler, api_key="nova_key_test")

    with pytest.raises(NovaPermissionError, match="Permission denied"):
        client.emails.export_csv()


# ==============================================================================
# Security & Error Handling
# ==============================================================================


def test_emails_auth_and_rate_limit_errors(mock_client_factory):
    def auth_handler(request: httpx.Request) -> httpx.Response:
        return json_response(status_code=401, message="Invalid API Key.")

    client = mock_client_factory(auth_handler, api_key="invalid_key")
    with pytest.raises(NovaAuthenticationError, match="Invalid API Key"):
        client.emails.list_logs()

    def rate_limit_handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=429,
            message="Rate limit exceeded.",
            headers={"Retry-After": "10"},
        )

    client_rate = mock_client_factory(
        rate_limit_handler, api_key="nova_key_test", max_retries=0
    )
    with pytest.raises(NovaRateLimitError, match="Rate limit exceeded"):
        client_rate.emails.list_logs()
