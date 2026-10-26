"""Tests for AnalyticsResource client."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import httpx
import pytest
from helpers import json_response

from nova_sdk.exceptions import (
    NovaAuthenticationError,
    NovaPermissionError,
    NovaServerError,
)

TENANT_ALPHA = "11111111-1111-1111-1111-111111111111"
TENANT_BETA = "22222222-2222-2222-2222-222222222222"


def test_dashboard_defaults(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/analytics/dashboard/"
        assert request.headers.get("X-Tenant-ID") == TENANT_ALPHA
        assert not request.url.params  # No date params by default
        return json_response(
            data={
                "total_contacts": 150,
                "new_contacts": 12,
                "email_overview": {
                    "total_email": 1200,
                    "sent": 1180,
                    "delivered": 1150,
                    "opened": 600,
                    "clicked": 250,
                    "bounced": 20,
                    "complaint": 2,
                    "failed": 8,
                },
                "recently_added_contacts": [
                    {
                        "id": "c1",
                        "username": "c1",
                        "email": "c1@example.com",
                        "first_name": "Alice",
                        "last_name": "Smith",
                    }
                ],
                "recently_failed_messages": [
                    {
                        "id": "m1",
                        "recipient_email": "bounced@example.com",
                        "subject": "Monthly Statement",
                        "status": "FAILED",
                        "created_at": "2026-10-24T10:00:00Z",
                    }
                ],
            }
        )

    client = mock_client_factory(
        handler, api_key="nova_key_test", tenant_id=TENANT_ALPHA
    )
    data = client.analytics.dashboard()

    assert data["total_contacts"] == 150
    assert data["new_contacts"] == 12
    assert data["email_overview"]["delivered"] == 1150
    assert data["email_overview"]["failed"] == 8
    assert len(data["recently_added_contacts"]) == 1
    assert len(data["recently_failed_messages"]) == 1


def test_dashboard_with_date_strings(mock_client_factory):
    captured_params: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/analytics/dashboard/"
        captured_params.update(dict(request.url.params))
        return json_response(
            data={
                "total_contacts": 50,
                "new_contacts": 5,
                "email_overview": {
                    "total_email": 100,
                    "sent": 95,
                    "delivered": 90,
                    "opened": 40,
                    "clicked": 15,
                    "bounced": 5,
                    "complaint": 0,
                    "failed": 0,
                },
                "recently_added_contacts": [],
                "recently_failed_messages": [],
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    data = client.analytics.dashboard(
        date_from="2026-10-01",
        date_to="2026-10-24",
    )

    assert captured_params["date_from"] == "2026-10-01"
    assert captured_params["date_to"] == "2026-10-24"
    assert data["total_contacts"] == 50


def test_dashboard_with_datetime_and_date_objects(mock_client_factory):
    captured_params: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_params.update(dict(request.url.params))
        return json_response(
            data={
                "total_contacts": 10,
                "new_contacts": 1,
                "email_overview": {
                    "total_email": 10,
                    "sent": 10,
                    "delivered": 10,
                    "opened": 5,
                    "clicked": 2,
                    "bounced": 0,
                    "complaint": 0,
                    "failed": 0,
                },
                "recently_added_contacts": [],
                "recently_failed_messages": [],
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")

    start_date = date(2026, 10, 1)
    end_datetime = datetime(2026, 10, 24, 18, 30, 0)

    client.analytics.dashboard(date_from=start_date, date_to=end_datetime)

    assert captured_params["date_from"] == "2026-10-01"
    assert captured_params["date_to"] == "2026-10-24T18:30:00"


def test_dashboard_tenant_override(mock_client_factory):
    captured_headers: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_headers.update(dict(request.headers))
        return json_response(
            data={
                "total_contacts": 0,
                "new_contacts": 0,
                "email_overview": {
                    "total_email": 0,
                    "sent": 0,
                    "delivered": 0,
                    "opened": 0,
                    "clicked": 0,
                    "bounced": 0,
                    "complaint": 0,
                    "failed": 0,
                },
                "recently_added_contacts": [],
                "recently_failed_messages": [],
            }
        )

    client = mock_client_factory(
        handler, api_key="nova_key_test", tenant_id=TENANT_ALPHA
    )
    client.analytics.dashboard(tenant_id=TENANT_BETA)

    assert captured_headers["x-tenant-id"] == TENANT_BETA
    # Client configuration tenant_id remains unchanged
    assert client.tenant_id == TENANT_ALPHA


def test_dashboard_error_mapping(mock_client_factory):
    def auth_fail(request: httpx.Request) -> httpx.Response:
        return json_response(status_code=401, message="Authentication required.")

    client = mock_client_factory(auth_fail, api_key="bad_key")
    with pytest.raises(NovaAuthenticationError, match="Authentication required"):
        client.analytics.dashboard()

    def perm_fail(request: httpx.Request) -> httpx.Response:
        return json_response(status_code=403, message="Not a member of this tenant.")

    client_perm = mock_client_factory(perm_fail, api_key="nova_key_test")
    with pytest.raises(NovaPermissionError, match="Not a member of this tenant"):
        client_perm.analytics.dashboard()

    def server_fail(request: httpx.Request) -> httpx.Response:
        return json_response(status_code=500, message="Analytics service degradation.")

    client_srv = mock_client_factory(server_fail, api_key="nova_key_test")
    with pytest.raises(NovaServerError, match="Analytics service degradation"):
        client_srv.analytics.dashboard()
