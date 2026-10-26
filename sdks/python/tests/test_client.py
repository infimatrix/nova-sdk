"""Tests for NovaClient initialization, lifecycle, and tenant context managers."""

from __future__ import annotations

import httpx
import pytest
from helpers import json_response

from nova_sdk import NovaClient, NovaConfig


def test_client_initialization_with_args():
    client = NovaClient(
        base_url="https://api.novamail.io",
        api_key="nova_key_test123",
        tenant_id="11111111-1111-1111-1111-111111111111",
        timeout=15.0,
    )
    assert client.config.base_url == "https://api.novamail.io"
    assert client.config.api_key == "nova_key_test123"
    assert client.tenant_id == "11111111-1111-1111-1111-111111111111"
    assert client.config.timeout == 15.0
    client.close()


def test_client_initialization_with_config_object():
    config = NovaConfig(
        base_url="https://api.novamail.io",
        api_key="nova_key_test123",
    )
    client = NovaClient(config=config)
    assert client.config is config
    client.close()


def test_client_context_manager_lifecycle():
    with NovaClient(base_url="http://localhost:8000") as client:
        assert not client.transport.is_closed

    assert client.transport.is_closed


def test_client_health(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/health/"
        return json_response(data={"status": "ok", "database": "healthy"})

    client = mock_client_factory(handler)
    health = client.health()
    assert health == {"status": "ok", "database": "healthy"}


def test_client_with_tenant_context_manager():
    client = NovaClient(tenant_id="11111111-1111-1111-1111-111111111111")
    assert client.tenant_id == "11111111-1111-1111-1111-111111111111"

    # Temporarily enter different tenant context
    with client.with_tenant("22222222-2222-2222-2222-222222222222"):
        assert client.tenant_id == "22222222-2222-2222-2222-222222222222"

    # Previous tenant context must be restored cleanly
    assert client.tenant_id == "11111111-1111-1111-1111-111111111111"


def test_client_with_tenant_restores_on_exception():
    client = NovaClient(tenant_id="11111111-1111-1111-1111-111111111111")

    with pytest.raises(RuntimeError):
        with client.with_tenant("22222222-2222-2222-2222-222222222222"):
            raise RuntimeError("Something failed inside tenant block")

    # Previous context restored even after exception
    assert client.tenant_id == "11111111-1111-1111-1111-111111111111"


def test_client_set_credentials():
    client = NovaClient()
    assert client.config.api_key is None
    assert client.config.access_token is None

    client.set_api_key("Bearer nova_key_updated")
    assert client.config.api_key == "nova_key_updated"

    client.set_auth_token("  bearer jwt_token_updated  ")
    assert client.config.access_token == "jwt_token_updated"


def test_client_resource_accessors():
    client = NovaClient(api_key="nova_key_test")
    assert hasattr(client, "auth")
    assert hasattr(client, "tenants")
    assert hasattr(client, "templates")
    assert hasattr(client, "contacts")
    assert hasattr(client, "emails")
    assert hasattr(client, "providers")
    assert hasattr(client, "webhooks")
    assert hasattr(client, "analytics")
    assert hasattr(client, "campaigns")
    assert hasattr(client.campaigns, "transactional")
    assert hasattr(client, "audit")
    assert hasattr(client.audit, "access_logs")
    client.close()
