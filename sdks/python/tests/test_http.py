"""Tests for HTTPTransport URL construction, headers, and envelope unwrapping."""

from __future__ import annotations

import httpx
import pytest
from helpers import json_response

from nova_sdk import NovaClient
from nova_sdk.exceptions import (
    NovaNotFoundError,
    NovaRedirectError,
    NovaServerError,
    NovaValidationError,
)


@pytest.mark.parametrize(
    "endpoint,expected_url",
    [
        # Endpoints with and without trailing slashes
        ("health", "https://api.novamail.io/api/v1/health/"),
        ("health/", "https://api.novamail.io/api/v1/health/"),
        ("/contacts", "https://api.novamail.io/api/v1/contacts/"),
        ("/contacts/", "https://api.novamail.io/api/v1/contacts/"),
        # Existing /api/v1/ prefix with and without slashes
        ("api/v1/templates", "https://api.novamail.io/api/v1/templates/"),
        ("api/v1/templates/", "https://api.novamail.io/api/v1/templates/"),
        ("/api/v1/templates", "https://api.novamail.io/api/v1/templates/"),
        ("/api/v1/templates/", "https://api.novamail.io/api/v1/templates/"),
        ("api/v1", "https://api.novamail.io/api/v1/"),
        ("/api/v1/", "https://api.novamail.io/api/v1/"),
        ("", "https://api.novamail.io/api/v1/"),
        ("/", "https://api.novamail.io/api/v1/"),
        # Query parameters: trailing slash appended to path, NOT to query string
        (
            "contacts?status=ACTIVE&limit=10",
            "https://api.novamail.io/api/v1/contacts/?status=ACTIVE&limit=10",
        ),
        (
            "contacts/?status=ACTIVE",
            "https://api.novamail.io/api/v1/contacts/?status=ACTIVE",
        ),
        (
            "/api/v1/emails/logs?page=2",
            "https://api.novamail.io/api/v1/emails/logs/?page=2",
        ),
        # Valid endpoints containing dots in path identifiers
        (
            "contacts/user.name@example.com",
            "https://api.novamail.io/api/v1/contacts/user.name@example.com/",
        ),
        (
            "contacts/user.name@example.com/",
            "https://api.novamail.io/api/v1/contacts/user.name@example.com/",
        ),
        (
            "versions/v1.0",
            "https://api.novamail.io/api/v1/versions/v1.0/",
        ),
        # CSV and export endpoints
        (
            "emails/logs/export",
            "https://api.novamail.io/api/v1/emails/logs/export/",
        ),
        (
            "emails/logs/export/",
            "https://api.novamail.io/api/v1/emails/logs/export/",
        ),
        (
            "contacts/sample-template",
            "https://api.novamail.io/api/v1/contacts/sample-template/",
        ),
        # File paths with known file extensions (no trailing slash added)
        (
            "exports/data.csv",
            "https://api.novamail.io/api/v1/exports/data.csv",
        ),
        (
            "schema.json",
            "https://api.novamail.io/api/v1/schema.json",
        ),
        (
            "exports/data.csv?format=raw",
            "https://api.novamail.io/api/v1/exports/data.csv?format=raw",
        ),
    ],
)
def test_build_url(endpoint: str, expected_url: str):
    client = NovaClient(base_url="https://api.novamail.io")
    assert client.transport.build_url(endpoint) == expected_url


def test_envelope_unwrapping(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/health/"
        return json_response(
            status_code=200,
            data={"status": "ok", "database": "healthy"},
            correlation_id="corr-abc-123",
        )

    client = mock_client_factory(handler)
    resp = client.transport.request("GET", "health/")

    assert resp.success is True
    assert resp.data == {"status": "ok", "database": "healthy"}
    assert resp.meta.correlation_id == "corr-abc-123"
    assert resp.meta.timestamp == "2026-10-24T08:00:00Z"


def test_204_no_content_handling(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=204, headers={"X-Correlation-ID": "del-corr-1"}
        )

    client = mock_client_factory(handler)
    resp = client.transport.request("DELETE", "templates/123/")

    assert resp.success is True
    assert resp.data is None
    assert resp.meta.correlation_id == "del-corr-1"


def test_csv_export_handling(mock_client_factory):
    csv_body = "Message ID,Sender,Recipient\nMSG001,alice@corp.com,bob@corp.com\n"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            headers={
                "Content-Type": "text/csv; charset=utf-8",
                "X-Correlation-ID": "csv-corr",
            },
            text=csv_body,
        )

    client = mock_client_factory(handler)
    resp = client.transport.request("GET", "emails/logs/export/")

    assert resp.success is True
    assert resp.data == csv_body
    assert resp.meta.correlation_id == "csv-corr"


def test_error_envelope_mapping(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=404,
            data={"id": "Template not found."},
            message="Template not found in workspace.",
            error_code="TEMPLATE_NOT_FOUND",
            correlation_id="err-corr-404",
        )

    client = mock_client_factory(handler)

    with pytest.raises(NovaNotFoundError) as exc_info:
        client.transport.request(
            "GET", "templates/00000000-0000-0000-0000-000000000000/"
        )

    err = exc_info.value
    assert err.status_code == 404
    assert err.error_code == "TEMPLATE_NOT_FOUND"
    assert "Template not found in workspace." in err.message
    assert err.correlation_id == "err-corr-404"


def test_per_request_tenant_override(mock_client_factory):
    captured_tenant_headers = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_tenant_headers.append(request.headers.get("X-Tenant-ID"))
        return json_response(data={"ok": True})

    client = mock_client_factory(
        handler,
        tenant_id="11111111-1111-1111-1111-111111111111",
    )

    # 1. Default request uses client-configured tenant
    client.transport.request("GET", "contacts/")
    assert captured_tenant_headers[-1] == "11111111-1111-1111-1111-111111111111"

    # 2. Per-request override uses the specified tenant without mutating client state
    client.transport.request(
        "GET", "contacts/", tenant_id="22222222-2222-2222-2222-222222222222"
    )
    assert captured_tenant_headers[-1] == "22222222-2222-2222-2222-222222222222"
    assert client.tenant_id == "11111111-1111-1111-1111-111111111111"

    # 3. Invalid UUID raises validation error immediately before network call
    with pytest.raises(NovaValidationError, match="valid UUID string"):
        client.transport.request("GET", "contacts/", tenant_id="invalid-uuid")


@pytest.mark.parametrize("status_code", [301, 302, 307])
def test_redirects_raise_nova_redirect_error(mock_client_factory, status_code: int):
    target_location = "https://api.novamail.io/api/v1/contacts/"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=status_code,
            headers={
                "Location": target_location,
                "X-Correlation-ID": f"red-{status_code}",
            },
            text=f"Redirecting to {target_location}",
        )

    client = mock_client_factory(handler)

    with pytest.raises(NovaRedirectError) as exc_info:
        client.transport.request("GET", "contacts")

    err = exc_info.value
    assert err.status_code == status_code
    assert err.location == target_location
    assert err.correlation_id == f"red-{status_code}"
    assert "Unexpected HTTP" in err.message
    assert target_location in err.message


def test_redirect_sanitizes_credentials_in_location(mock_client_factory):
    sensitive_location = "https://admin:super_secret_pw@api.novamail.io/api/v1/health/"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=301,
            headers={"Location": sensitive_location},
        )

    client = mock_client_factory(handler)

    with pytest.raises(NovaRedirectError) as exc_info:
        client.transport.request("GET", "health")

    err = exc_info.value
    assert "super_secret_pw" not in err.message
    assert "super_secret_pw" not in (err.location or "")
    assert "admin@" not in (err.location or "")
    assert err.location == "https://api.novamail.io/api/v1/health/"


def test_201_created_response_handling(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=201,
            data={"id": "new-item-123", "name": "Created Resource"},
            message="Resource created successfully.",
            correlation_id="corr-201",
        )

    client = mock_client_factory(handler)
    resp = client.transport.request("POST", "templates/", json={"name": "New"})

    assert resp.success is True
    assert resp.data == {"id": "new-item-123", "name": "Created Resource"}
    assert resp.meta.correlation_id == "corr-201"


def test_long_html_proxy_error_page_sanitization(mock_client_factory):
    html_error = (
        """<!DOCTYPE html>
<html>
<head><title>502 Bad Gateway</title></head>
<body bgcolor="white">
<center><h1>502 Bad Gateway</h1></center>
<hr><center>cloudflare / nginx proxy error details padding ... """
        + ("x" * 2000)
        + """</center>
</body>
</html>"""
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=502,
            headers={"Content-Type": "text/html; charset=utf-8"},
            text=html_error,
        )

    client = mock_client_factory(handler)

    with pytest.raises(NovaServerError) as exc_info:
        # allow_retry=False to immediately inspect error
        client.transport.request("GET", "health/", allow_retry=False)

    err = exc_info.value
    assert err.status_code == 502
    # The message should extract the concise title, NOT the raw HTML tags or 2000 characters of padding
    assert "502 Bad Gateway" in err.message
    assert "<!DOCTYPE html>" not in err.message
    assert "<center>" not in err.message
    assert len(err.message) <= 200


def test_long_plain_text_error_is_truncated(mock_client_factory):
    long_plain_error = "Server encountered an issue: " + ("abcdefghij" * 40)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=500,
            headers={"Content-Type": "text/plain"},
            text=long_plain_error,
        )

    client = mock_client_factory(handler)

    with pytest.raises(NovaServerError) as exc_info:
        client.transport.request("GET", "health/", allow_retry=False)

    err = exc_info.value
    assert err.status_code == 500
    assert len(err.message) <= 200
    assert err.message.endswith("...")


def test_request_raw_method(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert (
            request.headers.get("X-Tenant-ID") == "11111111-1111-1111-1111-111111111111"
        )
        return httpx.Response(
            status_code=200,
            headers={"Content-Type": "application/octet-stream"},
            content=b"binary-payload-stream",
        )

    client = mock_client_factory(handler)
    raw_resp = client.transport.request_raw(
        "GET",
        "health/",
        tenant_id="11111111-1111-1111-1111-111111111111",
    )

    assert isinstance(raw_resp, httpx.Response)
    assert raw_resp.status_code == 200
    assert raw_resp.content == b"binary-payload-stream"
    assert raw_resp.headers["Content-Type"] == "application/octet-stream"
