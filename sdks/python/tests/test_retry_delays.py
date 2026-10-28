"""Retry delays and request-level overrides, pinned from docs/conventions.md and docs/error-handling.md.

Found by mutation testing: the retry *count* was tested, but not how long the client waits, whether Retry-After is
honoured, or whether per-request headers / retry overrides are applied.
"""

from __future__ import annotations

import httpx
import pytest
from helpers import json_response

from nova_sdk.exceptions import NovaServerError


@pytest.fixture
def sleeps(monkeypatch):
    recorded: list[float] = []
    monkeypatch.setattr("nova_sdk.http.time.sleep", recorded.append)
    return recorded


def _always(status, headers=None):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(status_code=status, message="x", headers=headers)

    return handler


def test_backoff_doubles_each_attempt_without_jitter(mock_client_factory, sleeps):
    # docs: backoff = base * 2^attempt  ->  1, 2, 4 seconds for a 1 s base
    client = mock_client_factory(
        _always(503), max_retries=3, retry_backoff_factor=1.0, retry_jitter=False
    )
    with pytest.raises(NovaServerError):
        client.transport.request("GET", "health/")
    assert sleeps == [1.0, 2.0, 4.0]


def test_jittered_backoff_stays_between_half_and_full_delay(
    mock_client_factory, sleeps
):
    client = mock_client_factory(
        _always(503), max_retries=3, retry_backoff_factor=1.0, retry_jitter=True
    )
    with pytest.raises(NovaServerError):
        client.transport.request("GET", "health/")
    assert len(sleeps) == 3
    for attempt, delay in enumerate(sleeps):
        assert 0.5 * 2**attempt <= delay <= 1.0 * 2**attempt


@pytest.mark.parametrize(
    "header,expected",
    [("7", 7.0), ("0", 0.0), ("2.5", 2.5), ("120", 30.0)],  # docs: capped at 30 s
)
def test_retry_after_is_honoured_and_capped(
    mock_client_factory, sleeps, header, expected
):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) == 1:
            return json_response(
                status_code=429, message="slow", headers={"Retry-After": header}
            )
        return json_response(data={"ok": True})

    client = mock_client_factory(
        handler, max_retries=2, retry_backoff_factor=3.0, retry_jitter=False
    )
    assert client.transport.request("GET", "health/").data == {"ok": True}
    assert sleeps == [expected]


@pytest.mark.parametrize("header", ["soon", "", "Wed, 21 Oct 2026 07:28:00 GMT"])
def test_unusable_retry_after_falls_back_to_backoff(
    mock_client_factory, sleeps, header
):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) == 1:
            return json_response(
                status_code=503, message="x", headers={"Retry-After": header}
            )
        return json_response(data={})

    client = mock_client_factory(
        handler, max_retries=1, retry_backoff_factor=3.0, retry_jitter=False
    )
    client.transport.request("GET", "health/")
    assert sleeps == [3.0]


def test_connection_errors_back_off_the_same_way(mock_client_factory, sleeps):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    client = mock_client_factory(
        handler, max_retries=2, retry_backoff_factor=1.0, retry_jitter=False
    )
    with pytest.raises(Exception):  # noqa: B017 - the concrete class is asserted in test_http / conformance
        client.transport.request("GET", "health/")
    assert sleeps == [1.0, 2.0]


def test_allow_retry_overrides_the_method_default(mock_client_factory, sleeps):
    seen = {"post": 0, "get": 0}

    def post_handler(request: httpx.Request) -> httpx.Response:
        seen["post"] += 1
        return json_response(status_code=503, message="x")

    client = mock_client_factory(
        post_handler, max_retries=2, retry_backoff_factor=1.0, retry_jitter=False
    )
    with pytest.raises(NovaServerError):
        client.transport.request("POST", "emails/logs/send/", json={}, allow_retry=True)
    assert seen["post"] == 3  # explicit opt-in retries a POST

    def get_handler(request: httpx.Request) -> httpx.Response:
        seen["get"] += 1
        return json_response(status_code=503, message="x")

    client = mock_client_factory(
        get_handler, max_retries=2, retry_backoff_factor=1.0, retry_jitter=False
    )
    with pytest.raises(NovaServerError):
        client.transport.request("GET", "health/", allow_retry=False)
    assert seen["get"] == 1  # explicit opt-out stops a GET from retrying


def test_request_level_headers_and_correlation_id_are_sent(mock_client_factory):
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return json_response(data={})

    client = mock_client_factory(handler, api_key="nova_key_abc")
    client.transport.request(
        "GET", "health/", headers={"X-Custom": "v1"}, correlation_id="corr-77"
    )
    headers = captured[0].headers
    assert headers["x-custom"] == "v1"
    assert headers["x-correlation-id"] == "corr-77"
    assert (
        headers["authorization"] == "Bearer nova_key_abc"
    )  # per-request headers must not displace auth


@pytest.mark.parametrize("status", [300, 301, 303, 304, 399])
def test_every_3xx_is_an_unexpected_redirect(mock_client_factory, status):
    from nova_sdk.exceptions import NovaRedirectError

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, headers={"Location": "/elsewhere/"})

    client = mock_client_factory(handler)
    with pytest.raises(NovaRedirectError) as info:
        client.transport.request("GET", "health/")
    assert info.value.status_code == status


@pytest.mark.parametrize("status", [200, 201, 202, 203, 299])
def test_every_2xx_is_success(mock_client_factory, status):
    def handler(request: httpx.Request) -> httpx.Response:
        return (
            json_response(status_code=status, data={"n": status})
            if status != 299
            else httpx.Response(
                299, json={"success": True, "message": "ok", "data": {"n": 299}}
            )
        )

    client = mock_client_factory(handler)
    assert client.transport.request("GET", "health/").data == {"n": status}
