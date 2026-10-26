"""Tests for AuthResource and APIKeysResource clients."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from helpers import json_response

from nova_sdk.exceptions import (
    NovaAuthenticationError,
    NovaNotFoundError,
    NovaValidationError,
)


def test_auth_login_success(mock_client_factory):
    captured_request: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["method"] = request.method
        captured_request["path"] = request.url.path
        captured_request["body"] = json.loads(request.content.decode("utf-8"))
        return json_response(
            data={
                "access": "jwt_access_123",
                "refresh": "jwt_refresh_456",
                "user": {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "email": "user@novamail.io",
                    "username": "novauser",
                },
                "tenants": [
                    {
                        "id": "22222222-2222-2222-2222-222222222222",
                        "name": "Acme Corp",
                        "slug": "acme",
                        "role": "TENANT_ADMIN",
                    }
                ],
            }
        )

    client = mock_client_factory(handler)
    result = client.auth.login(email="user@novamail.io", password="supersecretpassword")

    assert captured_request["method"] == "POST"
    assert captured_request["path"] == "/api/v1/auth/login/"
    assert captured_request["body"] == {
        "email": "user@novamail.io",
        "password": "supersecretpassword",
    }
    assert result["access"] == "jwt_access_123"
    assert result["refresh"] == "jwt_refresh_456"
    assert result["user"]["email"] == "user@novamail.io"
    # By default, client auth token should not be mutated
    assert client.config.access_token is None


def test_auth_login_with_set_current_token(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            data={
                "access": "jwt_access_auto_apply",
                "refresh": "jwt_refresh_auto_apply",
                "user": {"id": "11111111-1111-1111-1111-111111111111"},
                "tenants": [],
            }
        )

    client = mock_client_factory(handler)
    client.auth.login(
        email="user@novamail.io",
        password="password123",
        set_current_token=True,
    )
    assert client.config.access_token == "jwt_access_auto_apply"
    assert (
        client.config.get_headers()["Authorization"] == "Bearer jwt_access_auto_apply"
    )


def test_auth_login_validation_errors(mock_client_factory):
    client = mock_client_factory(lambda r: httpx.Response(200))
    with pytest.raises(NovaValidationError, match="email must be a non-empty string"):
        client.auth.login(email="", password="password")

    with pytest.raises(
        NovaValidationError, match="password must be a non-empty string"
    ):
        client.auth.login(email="user@example.com", password="")


def test_auth_login_invalid_credentials_error(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=400,
            error_code="INVALID_CREDENTIALS",
            message="Invalid email or password.",
            data={"detail": "Invalid email or password."},
        )

    client = mock_client_factory(handler)
    with pytest.raises(NovaValidationError) as exc_info:
        client.auth.login(email="wrong@example.com", password="wrongpassword")

    assert exc_info.value.status_code == 400
    assert "Invalid email or password." in exc_info.value.message


def test_auth_refresh_token(mock_client_factory):
    captured_request: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["method"] = request.method
        captured_request["path"] = request.url.path
        captured_request["body"] = json.loads(request.content.decode("utf-8"))
        return json_response(data={"access": "new_access_token_789"})

    client = mock_client_factory(handler)
    res = client.auth.refresh("old_refresh_token_456")

    assert captured_request["method"] == "POST"
    assert captured_request["path"] == "/api/v1/auth/refresh/"
    assert captured_request["body"] == {"refresh": "old_refresh_token_456"}
    assert res["access"] == "new_access_token_789"


def test_auth_refresh_invalid_token_raises_auth_error(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=401,
            error_code="TOKEN_NOT_VALID",
            message="Token is invalid or expired",
            data={"detail": "Token is invalid or expired"},
        )

    client = mock_client_factory(handler)
    with pytest.raises(NovaAuthenticationError) as exc_info:
        client.auth.refresh("expired_token")

    assert exc_info.value.status_code == 401


def test_auth_logout(mock_client_factory):
    captured_request: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["method"] = request.method
        captured_request["path"] = request.url.path
        captured_request["auth"] = request.headers.get("Authorization")
        captured_request["body"] = json.loads(request.content.decode("utf-8"))
        return json_response(data={"message": "Successfully logged out."})

    client = mock_client_factory(handler, access_token="active_token")
    res = client.auth.logout("refresh_to_blacklist")

    assert captured_request["method"] == "POST"
    assert captured_request["path"] == "/api/v1/auth/logout/"
    assert captured_request["auth"] == "Bearer active_token"
    assert captured_request["body"] == {"refresh": "refresh_to_blacklist"}
    assert res["message"] == "Successfully logged out."


def test_auth_me(mock_client_factory):
    captured_request: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["method"] = request.method
        captured_request["path"] = request.url.path
        captured_request["auth"] = request.headers.get("Authorization")
        captured_request["tenant"] = request.headers.get("X-Tenant-ID")
        return json_response(
            data={
                "id": "11111111-1111-1111-1111-111111111111",
                "email": "swaraj@example.com",
                "username": "swaraj",
                "is_staff": False,
                "tenants": [
                    {
                        "id": "33333333-3333-3333-3333-333333333333",
                        "name": "Infimatrix",
                        "role": "TENANT_ADMIN",
                    }
                ],
                "current_tenant": {
                    "id": "33333333-3333-3333-3333-333333333333",
                    "name": "Infimatrix",
                },
                "current_role": "TENANT_ADMIN",
            }
        )

    client = mock_client_factory(
        handler,
        access_token="valid_jwt",
        tenant_id="33333333-3333-3333-3333-333333333333",
    )
    profile = client.auth.me()

    assert captured_request["method"] == "GET"
    assert captured_request["path"] == "/api/v1/auth/me/"
    assert captured_request["auth"] == "Bearer valid_jwt"
    assert captured_request["tenant"] == "33333333-3333-3333-3333-333333333333"
    assert profile["email"] == "swaraj@example.com"
    assert profile["current_role"] == "TENANT_ADMIN"


def test_api_keys_list(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/auth/api-keys/"
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
                        "id": "key-1",
                        "name": "CLI Key",
                        "key_prefix": "nova_key_cli",
                        "is_active": True,
                    },
                    {
                        "id": "key-2",
                        "name": "CI Key",
                        "key_prefix": "nova_key_ci",
                        "is_active": True,
                    },
                ],
            }
        )

    client = mock_client_factory(handler, access_token="jwt_token")
    keys = client.auth.api_keys.list()

    assert len(keys) == 2
    assert keys[0]["name"] == "CLI Key"
    assert keys[1]["name"] == "CI Key"
    assert keys.pagination.count == 2


def test_api_keys_create(mock_client_factory):
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/auth/api-keys/"
        captured_body.update(json.loads(request.content.decode("utf-8")))
        return json_response(
            status_code=201,
            data={
                "id": "99999999-9999-9999-9999-999999999999",
                "name": "Production Deploy Key",
                "key_prefix": "nova_key_prod",
                "api_key": "nova_key_super_secret_live_credential",
                "is_active": True,
                "expires_at": None,
            },
        )

    client = mock_client_factory(handler, access_token="jwt_token")
    created = client.auth.api_keys.create(name="Production Deploy Key")

    assert captured_body == {"name": "Production Deploy Key"}
    assert created["name"] == "Production Deploy Key"
    assert created["api_key"] == "nova_key_super_secret_live_credential"


def test_api_keys_revoke(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/api/v1/auth/api-keys/target-key-uuid/"
        return httpx.Response(status_code=204)

    client = mock_client_factory(handler, access_token="jwt_token")
    # Calling client.auth.revoke_api_key shortcut
    client.auth.revoke_api_key("target-key-uuid")


def test_api_keys_revoke_not_found(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=404,
            message="API Key not found.",
            error_code="NOT_FOUND",
        )

    client = mock_client_factory(handler, access_token="jwt_token")
    with pytest.raises(NovaNotFoundError):
        client.auth.api_keys.revoke("nonexistent-key")
