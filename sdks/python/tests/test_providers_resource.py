"""Tests for ProvidersResource client."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from helpers import json_response

from nova_sdk import (
    AuthenticationType,
    NovaAuthenticationError,
    NovaNotFoundError,
    NovaPermissionError,
    NovaRateLimitError,
    NovaServerError,
    NovaValidationError,
    ProvidersResource,
    ProviderType,
)

VALID_PROVIDER_ID = "55555555-5555-5555-5555-555555555555"
TENANT_ALPHA = "11111111-1111-1111-1111-111111111111"
TENANT_BETA = "22222222-2222-2222-2222-222222222222"


def test_providers_list_defaults(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/providers/"
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
                        "id": VALID_PROVIDER_ID,
                        "name": "Production SMTP",
                        "provider_type": ProviderType.SMTP,
                        "smtp_host": "mail.example.com",
                        "smtp_port": 587,
                        "has_password": True,
                        "has_secret_key": False,
                        "is_active": True,
                        "priority": 1,
                    },
                    {
                        "id": "66666666-6666-6666-6666-666666666666",
                        "name": "AWS SES Backup",
                        "provider_type": ProviderType.AWS_SES,
                        "aws_region": "us-east-1",
                        "has_password": False,
                        "has_secret_key": True,
                        "is_active": True,
                        "priority": 2,
                    },
                ],
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    providers = client.providers.list()

    assert len(providers) == 2
    assert providers[0]["name"] == "Production SMTP"
    assert providers[0]["provider_type"] == "SMTP"
    assert providers[1]["name"] == "AWS SES Backup"
    assert providers.pagination.count == 2
    names = [p["name"] for p in providers]
    assert names == ["Production SMTP", "AWS SES Backup"]


def test_providers_list_with_query_params(mock_client_factory):
    captured_params: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/providers/"
        captured_params.update(dict(request.url.params))
        return json_response(data={"results": [], "pagination": {"count": 0}})

    client = mock_client_factory(handler, api_key="nova_key_test")
    client.providers.list(
        search="mailpit",
        ordering="-priority",
        page=2,
        page_size=10,
        params={"custom_flag": "1"},
    )

    assert captured_params["search"] == "mailpit"
    assert captured_params["ordering"] == "-priority"
    assert captured_params["page"] == "2"
    assert captured_params["page_size"] == "10"
    assert captured_params["custom_flag"] == "1"


def test_providers_get_success(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == f"/api/v1/providers/{VALID_PROVIDER_ID}/"
        return json_response(
            data={
                "id": VALID_PROVIDER_ID,
                "name": "Demo SMTP Integration",
                "provider_type": ProviderType.SMTP,
                "senders": [
                    {
                        "name": "TG Demo",
                        "email": "demo@tradeganit.com",
                        "is_default": True,
                    }
                ],
                "smtp_host": "mailpit.tradeganit.com",
                "smtp_port": 1025,
                "tls_enabled": False,
                "authentication_type": AuthenticationType.BASIC,
                "smtp_user": "admin",
                "has_password": True,
                "aws_region": "us-east-1",
                "aws_access_key_id": "",
                "has_secret_key": False,
                "rate_limit_per_minute": 25,
                "is_active": True,
                "priority": 1,
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    provider = client.providers.get(VALID_PROVIDER_ID)

    assert provider["id"] == VALID_PROVIDER_ID
    assert provider["name"] == "Demo SMTP Integration"
    assert provider["has_password"] is True
    assert provider["has_secret_key"] is False
    assert "smtp_password" not in provider
    assert "aws_secret_access_key" not in provider


def test_providers_get_validation_error(mock_client_factory):
    client = mock_client_factory(lambda _: json_response())
    with pytest.raises(
        NovaValidationError, match="provider_id must be a non-empty string"
    ):
        client.providers.get("")
    with pytest.raises(
        NovaValidationError, match="provider_id must be a non-empty string"
    ):
        client.providers.get("   ")


def test_providers_create_smtp(mock_client_factory):
    captured_payload: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/providers/"
        nonlocal captured_payload
        captured_payload = json.loads(request.content.decode("utf-8"))
        return json_response(
            status_code=201,
            data={
                "id": VALID_PROVIDER_ID,
                "name": captured_payload["name"],
                "provider_type": captured_payload["provider_type"],
                "senders": captured_payload["senders"],
                "smtp_host": captured_payload["smtp_host"],
                "smtp_port": captured_payload["smtp_port"],
                "tls_enabled": captured_payload["tls_enabled"],
                "authentication_type": captured_payload["authentication_type"],
                "smtp_user": captured_payload["smtp_user"],
                "rate_limit_per_minute": captured_payload["rate_limit_per_minute"],
                "is_active": True,
                "priority": 1,
            },
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    res = client.providers.create(
        name="Demo SMTP Integration",
        provider_type=ProviderType.SMTP,
        senders=[
            {"name": "TG Demo", "email": "demo@tradeganit.com", "is_default": True},
            {"name": "Support", "email": "support@tradeganit.com", "is_default": False},
        ],
        smtp_host="mailpit.tradeganit.com",
        smtp_port=1025,
        tls_enabled=False,
        authentication_type=AuthenticationType.BASIC,
        smtp_user="admin",
        smtp_password="secretpassword",
        rate_limit_per_minute=25,
    )

    assert res["id"] == VALID_PROVIDER_ID
    assert res["name"] == "Demo SMTP Integration"
    assert captured_payload["name"] == "Demo SMTP Integration"
    assert captured_payload["provider_type"] == "SMTP"
    assert len(captured_payload["senders"]) == 2
    assert captured_payload["smtp_host"] == "mailpit.tradeganit.com"
    assert captured_payload["smtp_port"] == 1025
    assert captured_payload["smtp_password"] == "secretpassword"
    assert captured_payload["rate_limit_per_minute"] == 25


def test_providers_create_aws_ses(mock_client_factory):
    captured_payload: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/providers/"
        nonlocal captured_payload
        captured_payload = json.loads(request.content.decode("utf-8"))
        return json_response(
            status_code=201,
            data={
                "id": "77777777-7777-7777-7777-777777777777",
                "name": captured_payload["name"],
                "provider_type": captured_payload["provider_type"],
                "aws_region": captured_payload["aws_region"],
                "aws_access_key_id": captured_payload["aws_access_key_id"],
                "rate_limit_per_minute": 50,
            },
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    res = client.providers.create(
        name="Production AWS SES",
        provider_type=ProviderType.AWS_SES,
        aws_region="us-east-1",
        aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
        aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        rate_limit_per_minute=50,
        priority=2,
    )

    assert res["id"] == "77777777-7777-7777-7777-777777777777"
    assert captured_payload["provider_type"] == "AWS_SES"
    assert captured_payload["aws_region"] == "us-east-1"
    assert captured_payload["aws_access_key_id"] == "AKIAIOSFODNN7EXAMPLE"
    assert (
        captured_payload["aws_secret_access_key"]
        == "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    )
    assert captured_payload["priority"] == 2


def test_providers_create_validation_errors(mock_client_factory):
    client = mock_client_factory(lambda _: json_response())

    with pytest.raises(NovaValidationError, match="name must be a non-empty string"):
        client.providers.create(name="")

    with pytest.raises(
        NovaValidationError, match="senders must be a list of sender dictionaries"
    ):
        client.providers.create(name="Valid", senders="not-a-list")  # type: ignore[arg-type]

    with pytest.raises(
        NovaValidationError, match="Each sender entry must be a dictionary"
    ):
        client.providers.create(name="Valid", senders=["invalid-sender"])  # type: ignore[list-item]

    with pytest.raises(
        NovaValidationError, match="must contain a non-empty 'email' field"
    ):
        client.providers.create(name="Valid", senders=[{"name": "No Email"}])


def test_providers_update(mock_client_factory):
    captured_payload: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == f"/api/v1/providers/{VALID_PROVIDER_ID}/"
        nonlocal captured_payload
        captured_payload = json.loads(request.content.decode("utf-8"))
        return json_response(
            data={
                "id": VALID_PROVIDER_ID,
                "name": captured_payload.get("name", "Demo SMTP"),
                "smtp_port": captured_payload.get("smtp_port", 587),
                "tls_enabled": captured_payload.get("tls_enabled", True),
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    res = client.providers.update(
        VALID_PROVIDER_ID,
        name="Updated SMTP Integration",
        smtp_port=465,
        tls_enabled=True,
    )

    assert res["name"] == "Updated SMTP Integration"
    assert res["smtp_port"] == 465
    assert captured_payload["name"] == "Updated SMTP Integration"
    assert captured_payload["smtp_port"] == 465
    assert captured_payload["tls_enabled"] is True


def test_providers_update_validation(mock_client_factory):
    client = mock_client_factory(lambda _: json_response())
    with pytest.raises(
        NovaValidationError, match="provider_id must be a non-empty string"
    ):
        client.providers.update("", name="Test")


def test_providers_delete_success(mock_client_factory):
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == f"/api/v1/providers/{VALID_PROVIDER_ID}/"
        nonlocal called
        called = True
        return httpx.Response(status_code=204)

    client = mock_client_factory(handler, api_key="nova_key_test")
    result = client.providers.delete(VALID_PROVIDER_ID)

    assert called is True
    assert result is None


def test_providers_delete_validation(mock_client_factory):
    client = mock_client_factory(lambda _: json_response())
    with pytest.raises(
        NovaValidationError, match="provider_id must be a non-empty string"
    ):
        client.providers.delete("   ")


def test_providers_types(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/providers/types/"
        return json_response(
            data=[
                {
                    "key": "SMTP",
                    "label": "SMTP",
                    "description": "Connect via SMTP server",
                },
                {
                    "key": "AWS_SES",
                    "label": "Amazon SES",
                    "description": "Connect via AWS Simple Email Service",
                },
                {
                    "key": "SENDGRID",
                    "label": "SendGrid",
                    "description": "Connect via SendGrid API",
                },
                {
                    "key": "MAILGUN",
                    "label": "Mailgun",
                    "description": "Connect via Mailgun API",
                },
            ]
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    types = client.providers.types()

    assert len(types) == 4
    keys = [t["key"] for t in types]
    assert "SMTP" in keys
    assert "AWS_SES" in keys
    assert "SENDGRID" in keys
    assert "MAILGUN" in keys


def test_providers_test_email_dispatch(mock_client_factory):
    captured_payload: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == f"/api/v1/providers/{VALID_PROVIDER_ID}/test/"
        nonlocal captured_payload
        captured_payload = json.loads(request.content.decode("utf-8"))
        return json_response(
            data={
                "success": True,
                "message": f"Test email dispatched successfully to {captured_payload['recipient_email']}.",
                "message_id": "MSG001",
                "task_id": "celery-task-uuid-12345",
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    res = client.providers.test(
        VALID_PROVIDER_ID,
        recipient_email="test.recipient@tradeganit.com",
    )

    assert res["success"] is True
    assert "dispatched successfully" in res["message"]
    assert res["message_id"] == "MSG001"
    assert res["task_id"] == "celery-task-uuid-12345"
    assert captured_payload["recipient_email"] == "test.recipient@tradeganit.com"


def test_providers_test_validation(mock_client_factory):
    client = mock_client_factory(lambda _: json_response())

    with pytest.raises(
        NovaValidationError, match="provider_id must be a non-empty string"
    ):
        client.providers.test("", recipient_email="user@example.com")

    with pytest.raises(
        NovaValidationError, match="recipient_email must be a non-empty string"
    ):
        client.providers.test(VALID_PROVIDER_ID, recipient_email="")


def test_providers_tenant_override(mock_client_factory):
    captured_tenant_headers: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_tenant_headers.append(request.headers.get("X-Tenant-ID"))
        return json_response(data={"results": [], "pagination": {"count": 0}})

    client = mock_client_factory(
        handler,
        api_key="nova_key_test",
        tenant_id=TENANT_ALPHA,
    )

    # 1. Default request uses client-level tenant
    client.providers.list()
    assert captured_tenant_headers[-1] == TENANT_ALPHA

    # 2. Per-request override uses specified tenant
    client.providers.list(tenant_id=TENANT_BETA)
    assert captured_tenant_headers[-1] == TENANT_BETA

    # 3. Client's active tenant must remain unchanged
    assert client.tenant_id == TENANT_ALPHA


def test_providers_no_automatic_retries_on_side_effects(mock_client_factory):
    """Verify create, update, delete, and test are NOT retried on 500/503 errors."""
    call_counts = {"create": 0, "update": 0, "delete": 0, "test": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        method = request.method
        path = request.url.path

        if method == "POST" and path == "/api/v1/providers/":
            call_counts["create"] += 1
            return json_response(status_code=500, message="Server error on create")
        elif method == "PATCH":
            call_counts["update"] += 1
            return json_response(status_code=503, message="Unavailable on update")
        elif method == "DELETE":
            call_counts["delete"] += 1
            return json_response(status_code=500, message="Server error on delete")
        elif method == "POST" and "test" in path:
            call_counts["test"] += 1
            return json_response(status_code=500, message="Server error on test")

        return json_response()

    client = mock_client_factory(handler, api_key="nova_key_test", max_retries=3)

    # create
    with pytest.raises(NovaServerError):
        client.providers.create(name="Failing Provider")
    assert call_counts["create"] == 1

    # update
    with pytest.raises(NovaServerError):
        client.providers.update(VALID_PROVIDER_ID, name="New Name")
    assert call_counts["update"] == 1

    # delete
    with pytest.raises(NovaServerError):
        client.providers.delete(VALID_PROVIDER_ID)
    assert call_counts["delete"] == 1

    # test
    with pytest.raises(NovaServerError):
        client.providers.test(VALID_PROVIDER_ID, recipient_email="qa@example.com")
    assert call_counts["test"] == 1


def test_providers_credential_redaction_in_exceptions(mock_client_factory):
    """Ensure raw secret credentials are never exposed in exception strings or representations."""
    secret_pass = "super_secret_smtp_password_999!"

    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=400,
            message="Invalid provider configuration.",
            data={"smtp_password": ["Password does not meet complexity requirements."]},
        )

    client = mock_client_factory(handler, api_key="nova_key_test")

    with pytest.raises(NovaValidationError) as exc_info:
        client.providers.create(
            name="Secure Provider",
            smtp_password=secret_pass,
        )

    err = exc_info.value
    err_str = str(err)
    err_repr = repr(err)

    # Raw secret must never be leaked into exception messages or representations
    assert secret_pass not in err_str
    assert secret_pass not in err_repr
    assert "Invalid provider configuration" in err_str


def test_providers_typed_api_exceptions(mock_client_factory):
    status_map = [
        (400, NovaValidationError),
        (401, NovaAuthenticationError),
        (403, NovaPermissionError),
        (404, NovaNotFoundError),
        (429, NovaRateLimitError),
        (500, NovaServerError),
        (502, NovaServerError),
    ]

    for status_code, exc_class in status_map:

        def handler(request: httpx.Request, sc=status_code) -> httpx.Response:
            return json_response(status_code=sc, message=f"Error {sc}")

        client = mock_client_factory(handler, api_key="nova_key_test")
        with pytest.raises(exc_class):
            client.providers.get(VALID_PROVIDER_ID)


def test_providers_client_registration_and_exports():
    """Verify ProvidersResource is cleanly exposed on NovaClient and package root."""
    from nova_sdk import NovaClient

    client = NovaClient(api_key="nova_key_test")
    assert isinstance(client.providers, ProvidersResource)
    assert ProviderType.SMTP == "SMTP"
    assert ProviderType.AWS_SES == "AWS_SES"
    assert ProviderType.SENDGRID == "SENDGRID"
    assert ProviderType.MAILGUN == "MAILGUN"
    assert ProviderType.POSTMARK == "POSTMARK"
    assert ProviderType.MOCK == "MOCK"
    assert AuthenticationType.BASIC == "BASIC"
    assert AuthenticationType.NONE == "NONE"
    assert AuthenticationType.OAUTH2 == "OAUTH2"
    client.close()
