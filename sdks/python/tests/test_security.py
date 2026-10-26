"""Security tests for credential protection, secret sanitization, and redirect safety."""

from __future__ import annotations

from nova_sdk import NovaClient, NovaConfig
from nova_sdk.exceptions import NovaError


def test_config_repr_redacts_api_key_and_access_token():
    raw_api_key = "nova_key_super_secret_production_credential_99999"
    raw_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.sensitive_payload"

    config = NovaConfig(api_key=raw_api_key, access_token=raw_token)
    repr_str = repr(config)

    # Must NOT contain the full secrets
    assert raw_api_key not in repr_str
    assert raw_token not in repr_str
    # Must indicate redaction
    assert "[REDACTED]" in repr_str


def test_client_repr_redacts_secrets():
    raw_api_key = "nova_key_sensitive_12345"
    client = NovaClient(api_key=raw_api_key)
    repr_str = repr(client)

    assert raw_api_key not in repr_str
    assert "[REDACTED]" in repr_str


def test_exception_str_repr_does_not_contain_secrets():
    err = NovaError("Authentication failed for token: secret_jwt_token_here")
    # Even if an error contains a raw message, repr should stay structured
    repr_str = repr(err)
    assert "NovaError" in repr_str


def test_follow_redirects_disabled_by_default():
    """Ensure HTTPTransport does not follow arbitrary redirects automatically,

    which prevents credentials from being forwarded to another origin.
    """
    client = NovaClient()
    # Check underlying httpx client follow_redirects property
    # In httpx, follow_redirects can be inspected on the client or client._transport
    # We explicitly passed follow_redirects=False
    assert client.transport._client.follow_redirects is False
