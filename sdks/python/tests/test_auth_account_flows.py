"""Tests for registration and password recovery endpoints on AuthResource."""

from __future__ import annotations

import json

import httpx
import pytest
from helpers import json_response

from nova_sdk import schemas
from nova_sdk.exceptions import (
    NovaRateLimitError,
    NovaServerError,
    NovaValidationError,
)


def test_register_posts_payload_and_returns_typed_model(mock_client_factory):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/auth/register/"
        assert "authorization" not in request.headers
        captured.update(json.loads(request.content))
        return json_response(
            status_code=201,
            data={
                "access": "jwt-access",
                "refresh": "jwt-refresh",
                "user": {"id": "u1", "email": "new@example.com"},
                "tenants": [],
            },
        )

    client = mock_client_factory(handler)
    result = client.auth.register(
        email=" new@example.com ",
        password="Str0ng-Passw0rd!x",
        first_name="Ada",
        organization_name="Analytical Engines",
        set_current_token=True,
    )
    assert isinstance(result, schemas.UserRegister)
    assert result.access == "jwt-access"
    assert captured == {
        "email": "new@example.com",
        "password": "Str0ng-Passw0rd!x",
        "first_name": "Ada",
        "organization_name": "Analytical Engines",
    }
    assert client.config.access_token == "jwt-access"


@pytest.mark.parametrize("email,password", [("", "x"), ("a@b.co", "")])
def test_register_validates_required_fields(mock_client_factory, email, password):
    client = mock_client_factory(lambda r: json_response())
    with pytest.raises(NovaValidationError):
        client.auth.register(email=email, password=password)


def test_register_is_never_retried(mock_client_factory):
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return json_response(status_code=503, message="down")

    client = mock_client_factory(handler, max_retries=3, retry_backoff_factor=0.01)
    with pytest.raises(NovaServerError):
        client.auth.register(email="a@b.co", password="Str0ng-Passw0rd!x")
    assert calls == 1


def test_forgot_password(mock_client_factory):
    def handler(request):
        assert request.url.path == "/api/v1/auth/forgot-password/"
        assert json.loads(request.content) == {"email": "a@b.co"}
        return json_response(
            data={"detail": "If the account exists...", "message": "ok"}
        )

    client = mock_client_factory(handler)
    result = client.auth.forgot_password(" a@b.co ")
    assert isinstance(result, schemas.ForgotPasswordResponse)
    assert result.message == "ok"


def test_forgot_password_rate_limited(mock_client_factory):
    def handler(request):
        return json_response(
            status_code=429,
            message="Throttled",
            headers={"Retry-After": "7"},
        )

    client = mock_client_factory(handler)
    with pytest.raises(NovaRateLimitError) as exc:
        client.auth.forgot_password("a@b.co")
    assert exc.value.retry_after == 7


def test_validate_reset_token(mock_client_factory):
    def handler(request):
        assert request.url.path == "/api/v1/auth/reset-password/validate/"
        assert json.loads(request.content) == {"uid": "abc", "token": "tok"}
        return json_response(data={"valid": True, "detail": "ok"})

    client = mock_client_factory(handler)
    assert client.auth.validate_reset_token(uid="abc", token="tok").valid is True


def test_reset_password(mock_client_factory):
    def handler(request):
        assert request.url.path == "/api/v1/auth/reset-password/"
        assert json.loads(request.content) == {
            "uid": "abc",
            "token": "tok",
            "new_password": "N3w-Passw0rd!x",
            "confirm_password": "N3w-Passw0rd!x",
        }
        return json_response(data={"detail": "done", "message": "done"})

    client = mock_client_factory(handler)
    result = client.auth.reset_password(
        uid="abc",
        token="tok",
        new_password="N3w-Passw0rd!x",
        confirm_password="N3w-Passw0rd!x",
    )
    assert result.detail == "done"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"uid": "", "token": "t", "new_password": "x"},
        {"uid": "u", "token": "", "new_password": "x"},
        {"uid": "u", "token": "t", "new_password": ""},
    ],
)
def test_reset_password_validates_inputs(mock_client_factory, kwargs):
    client = mock_client_factory(lambda r: json_response())
    with pytest.raises(NovaValidationError):
        client.auth.reset_password(**kwargs)


def test_change_password_sends_auth_and_tenant(mock_client_factory):
    tenant = "11111111-1111-1111-1111-111111111111"

    def handler(request):
        assert request.url.path == "/api/v1/auth/change-password/"
        assert request.headers["authorization"] == "Bearer jwt"
        assert request.headers["x-tenant-id"] == tenant
        assert json.loads(request.content)["old_password"] == "old-pass"
        return json_response(data={"detail": "changed", "message": "changed"})

    client = mock_client_factory(handler, access_token="jwt", tenant_id=tenant)
    result = client.auth.change_password(
        old_password="old-pass",
        new_password="new-pass-1",
        confirm_password="new-pass-1",
    )
    assert result.message == "changed"


def test_change_password_validation_error_details(mock_client_factory):
    def handler(request):
        return json_response(
            status_code=400,
            message="old_password: wrong",
            error_code="VALIDATION_ERROR",
            data={"old_password": ["wrong"]},
        )

    client = mock_client_factory(handler, access_token="jwt")
    with pytest.raises(NovaValidationError) as exc:
        client.auth.change_password(
            old_password="x", new_password="y", confirm_password="y"
        )
    assert exc.value.details == {"old_password": ["wrong"]}
