"""Mock helpers and response builders for SDK tests."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx


def create_mock_transport(
    handler: Callable[[httpx.Request], httpx.Response],
) -> httpx.MockTransport:
    """Create an httpx.MockTransport with a custom request handler."""
    return httpx.MockTransport(handler)


def json_response(
    status_code: int = 200,
    data: Any = None,
    success: bool = True,
    message: str = "Operation completed successfully.",
    correlation_id: str = "test-corr-12345",
    error_code: str | None = None,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    """Construct a mock HTTP response matching the Nova envelope specification."""
    resp_headers = {
        "Content-Type": "application/json",
        "X-Correlation-ID": correlation_id,
    }
    if headers:
        resp_headers.update(headers)

    if status_code >= 400:
        payload = {
            "success": False,
            "message": message,
            "data": None,
            "error": {
                "code": error_code or "API_ERROR",
                "message": message,
                "details": data or {},
            },
            "meta": {
                "timestamp": "2026-10-24T08:00:00Z",
                "correlation_id": correlation_id,
            },
        }
    else:
        payload = {
            "success": success,
            "message": message,
            "data": data,
            "errors": None,
            "meta": {
                "timestamp": "2026-10-24T08:00:00Z",
                "correlation_id": correlation_id,
            },
        }

    return httpx.Response(
        status_code=status_code,
        headers=resp_headers,
        content=json.dumps(payload).encode("utf-8"),
    )
