"""Tests for NovaConfig validation and initialization."""

from __future__ import annotations

import pytest

from nova_sdk.config import NovaConfig
from nova_sdk.exceptions import NovaValidationError


def test_default_config():
    config = NovaConfig()
    assert config.base_url == "http://localhost:8000"
    assert config.timeout == 30.0
    assert config.max_retries == 3
    assert config.verify_ssl is True
    assert config.api_key is None
    assert config.access_token is None
    assert config.tenant_id is None


def test_base_url_normalization():
    # Strips trailing slash
    cfg1 = NovaConfig(base_url="https://api.novamail.io/")
    assert cfg1.base_url == "https://api.novamail.io"

    # Strips trailing /api/v1 if inadvertently supplied
    cfg2 = NovaConfig(base_url="https://api.novamail.io/api/v1")
    assert cfg2.base_url == "https://api.novamail.io"

    cfg3 = NovaConfig(base_url="https://api.novamail.io/api/v1/")
    assert cfg3.base_url == "https://api.novamail.io"


def test_base_url_invalid_schemes():
    with pytest.raises(NovaValidationError, match="Must be 'http' or 'https'"):
        NovaConfig(base_url="ftp://invalid.com")

    with pytest.raises(NovaValidationError, match="non-empty string"):
        NovaConfig(base_url="")


def test_timeout_validation():
    with pytest.raises(NovaValidationError, match="positive number"):
        NovaConfig(timeout=0)

    with pytest.raises(NovaValidationError, match="positive number"):
        NovaConfig(timeout=-5.0)


def test_max_retries_validation():
    with pytest.raises(NovaValidationError, match="non-negative integer"):
        NovaConfig(max_retries=-1)

    with pytest.raises(NovaValidationError, match="cannot exceed 10"):
        NovaConfig(max_retries=15)


def test_tenant_id_validation():
    # Valid UUID
    valid_uuid = "12345678-1234-5678-1234-567812345678"
    config = NovaConfig(tenant_id=valid_uuid)
    assert config.tenant_id == valid_uuid

    # Invalid UUID
    with pytest.raises(NovaValidationError, match="valid UUID string"):
        NovaConfig(tenant_id="not-a-uuid")


def test_headers_assembly():
    config = NovaConfig(
        api_key="nova_key_test123",
        tenant_id="12345678-1234-5678-1234-567812345678",
        default_headers={"X-Custom-Client": "MyClient/1.0"},
    )
    headers = config.get_headers()
    assert headers["Authorization"] == "Bearer nova_key_test123"
    assert headers["X-Tenant-ID"] == "12345678-1234-5678-1234-567812345678"
    assert headers["X-Custom-Client"] == "MyClient/1.0"
    assert headers["Accept"] == "application/json"


def test_access_token_takes_effect_when_no_api_key():
    config = NovaConfig(access_token="jwt_token_abc")
    headers = config.get_headers()
    assert headers["Authorization"] == "Bearer jwt_token_abc"


def test_api_key_preferred_over_access_token():
    config = NovaConfig(api_key="nova_key_override", access_token="jwt_token_abc")
    headers = config.get_headers()
    assert headers["Authorization"] == "Bearer nova_key_override"


@pytest.mark.parametrize(
    "raw_key,expected_header",
    [
        ("nova_key_live_123", "Bearer nova_key_live_123"),
        ("Bearer nova_key_live_123", "Bearer nova_key_live_123"),
        ("bearer nova_key_live_123", "Bearer nova_key_live_123"),
        ("BEARER nova_key_live_123", "Bearer nova_key_live_123"),
        ("  Bearer   nova_key_live_123  ", "Bearer nova_key_live_123"),
        ("Bearer Bearer nova_key_live_123", "Bearer nova_key_live_123"),
    ],
)
def test_credential_normalization_bearer_prefix(raw_key: str, expected_header: str):
    config = NovaConfig(api_key=raw_key)
    headers = config.get_headers()
    assert headers["Authorization"] == expected_header
    # Ensure config.api_key is normalized
    assert config.api_key == "nova_key_live_123"


def test_access_token_bearer_normalization():
    config = NovaConfig(access_token="  bearer   jwt_token_xyz  ")
    headers = config.get_headers()
    assert headers["Authorization"] == "Bearer jwt_token_xyz"
    assert config.access_token == "jwt_token_xyz"


def test_empty_or_bearer_only_credential_handling():
    config = NovaConfig(api_key="Bearer ", access_token="jwt_valid")
    headers = config.get_headers()
    # Empty Bearer prefix should not count as api_key, falls through to access_token
    assert headers["Authorization"] == "Bearer jwt_valid"


def test_repr_redaction_with_bearer_prefix():
    config = NovaConfig(api_key="Bearer nova_key_production_secret_99999")
    repr_str = repr(config)
    assert "nova_key...[REDACTED]" in repr_str
    assert "production_secret_99999" not in repr_str
    assert "Bearer Bearer" not in repr_str
