"""Tests for safe retry mechanics, bounded backoff, and side-effect protections."""

from __future__ import annotations

import httpx
import pytest
from helpers import json_response

from nova_sdk.exceptions import (
    NovaAuthenticationError,
    NovaServerError,
)


def test_idempotent_get_retries_on_transient_server_error(mock_client_factory):
    """Verify that idempotent GET requests retry on 503 status up to max_retries."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return json_response(status_code=503, message="Temporary service outage.")
        return json_response(status_code=200, data={"status": "recovered"})

    client = mock_client_factory(
        handler,
        max_retries=3,
        retry_backoff_factor=0.01,  # Fast tests
    )

    response = client.transport.request("GET", "templates/")
    assert response.success is True
    assert response.data == {"status": "recovered"}
    assert call_count == 3


def test_idempotent_get_exhausts_retries_and_raises(mock_client_factory):
    """Verify that persistent 503 errors stop after max_retries and raise NovaServerError."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return json_response(status_code=503, message="Persistent outage.")

    client = mock_client_factory(
        handler,
        max_retries=2,
        retry_backoff_factor=0.01,
    )

    with pytest.raises(NovaServerError) as exc_info:
        client.transport.request("GET", "health/")

    assert exc_info.value.status_code == 503
    # Initial attempt + 2 retries = 3 attempts total
    assert call_count == 3


def test_post_requests_never_automatically_retried(mock_client_factory):
    """CRITICAL SAFETY TEST:

    Side-effect operations like POST must NEVER be retried automatically,
    even when receiving 500 or 503, to prevent duplicate emails or dispatch side effects.
    """
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return json_response(status_code=503, message="Internal email backend error.")

    client = mock_client_factory(
        handler,
        max_retries=5,  # Even with high max_retries configured
        retry_backoff_factor=0.01,
    )

    with pytest.raises(NovaServerError):
        client.transport.request(
            "POST",
            "emails/logs/send/",
            json={"recipient_email": "test@corp.com", "subject": "Hello"},
        )

    # Must be executed exactly once and NEVER retried
    assert call_count == 1


def test_put_patch_delete_not_retried_by_default(mock_client_factory):
    """Verify that mutation methods PUT, PATCH, DELETE are not automatically retried."""
    for method in ("PUT", "PATCH", "DELETE"):
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return json_response(status_code=500, message="Database error.")

        client = mock_client_factory(handler, max_retries=3, retry_backoff_factor=0.01)

        with pytest.raises(NovaServerError):
            client.transport.request(
                method, "templates/123/", json={"name": "New Name"}
            )

        assert call_count == 1, f"{method} request was retried unexpectedly!"


def test_client_errors_never_retried(mock_client_factory):
    """Verify that 400 Validation and 401 Authentication errors are not retried."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return json_response(status_code=401, message="Invalid Bearer Token")

    client = mock_client_factory(handler, max_retries=3, retry_backoff_factor=0.01)

    with pytest.raises(NovaAuthenticationError):
        client.transport.request("GET", "auth/me/")

    assert call_count == 1


def test_respects_retry_after_header(mock_client_factory):
    """Verify that 429 parses Retry-After header and retries on idempotent GET."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return json_response(
                status_code=429,
                message="Too many requests",
                headers={"Retry-After": "0.05"},
            )
        return json_response(status_code=200, data={"ok": True})

    client = mock_client_factory(handler, max_retries=2, retry_backoff_factor=0.01)
    resp = client.transport.request("GET", "analytics/dashboard/")
    assert resp.success is True
    assert call_count == 2
