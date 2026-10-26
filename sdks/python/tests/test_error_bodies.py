"""Tests for error parsing of both enveloped and legacy backend error bodies."""

from __future__ import annotations

import httpx
import pytest

from nova_sdk.exceptions import NovaError, NovaPermissionError, NovaValidationError


def _raw(status: int, body: dict) -> httpx.Response:
    return httpx.Response(status, json=body, headers={"X-Correlation-ID": "cid-1"})


def test_string_error_field_becomes_message(mock_client_factory):
    client = mock_client_factory(
        lambda r: _raw(400, {"error": "Tenant context required."}), api_key="k"
    )
    with pytest.raises(NovaError) as exc:
        client.contacts.bulk_delete(["11111111-1111-1111-1111-111111111111"])
    assert "Tenant context required." in str(exc.value)
    assert exc.value.correlation_id == "cid-1"


def test_detail_only_body(mock_client_factory):
    client = mock_client_factory(
        lambda r: _raw(403, {"detail": "No tenant context."}), api_key="k"
    )
    with pytest.raises(NovaPermissionError) as exc:
        client.audit.access_logs.stats()
    assert "No tenant context." in str(exc.value)


def test_enveloped_validation_error_exposes_details(mock_client_factory):
    body = {
        "success": False,
        "message": "name: This field is required.",
        "data": None,
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "name: This field is required.",
            "details": {"name": ["This field is required."]},
        },
        "errors": {},
        "meta": {"correlation_id": "cid-2"},
    }
    client = mock_client_factory(lambda r: _raw(400, body), api_key="k")
    with pytest.raises(NovaValidationError) as exc:
        client.tenants.create(name="x", slug="x")
    assert exc.value.error_code == "VALIDATION_ERROR"
    assert exc.value.details == {"name": ["This field is required."]}
    assert exc.value.correlation_id == "cid-2"
