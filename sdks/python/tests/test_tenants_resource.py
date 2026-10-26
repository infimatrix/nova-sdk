"""Tests for TenantsResource and TenantMembershipsResource clients."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from helpers import json_response

from nova_sdk.exceptions import (
    NovaNotFoundError,
    NovaPermissionError,
    NovaValidationError,
)
from nova_sdk.models import Role, TenantStatus

VALID_TENANT_ID = "11111111-1111-1111-1111-111111111111"
VALID_MEMBER_ID = "22222222-2222-2222-2222-222222222222"


def test_tenants_list(mock_client_factory):
    captured_params: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/tenants/"
        captured_params.update(dict(request.url.params))
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
                        "id": VALID_TENANT_ID,
                        "name": "Infimatrix",
                        "slug": "infimatrix",
                        "status": "ACTIVE",
                    },
                    {
                        "id": "33333333-3333-3333-3333-333333333333",
                        "name": "Acme",
                        "slug": "acme",
                        "status": "ACTIVE",
                    },
                ],
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    page = client.tenants.list(params={"page": 1})

    assert captured_params.get("page") == "1"
    assert len(page) == 2
    assert page[0]["name"] == "Infimatrix"
    assert page[1]["slug"] == "acme"
    assert page.pagination.count == 2
    # Check iteration protocol
    names = [t["name"] for t in page]
    assert names == ["Infimatrix", "Acme"]


def test_tenants_create(mock_client_factory):
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/tenants/"
        captured_body.update(json.loads(request.content.decode("utf-8")))
        return json_response(
            status_code=201,
            data={
                "id": VALID_TENANT_ID,
                "name": "New Organization",
                "slug": "new-org",
                "website": "https://neworg.com",
                "logo_url": "https://neworg.com/logo.png",
                "status": TenantStatus.ACTIVE,
            },
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    tenant = client.tenants.create(
        name="New Organization",
        slug="new-org",
        website="https://neworg.com",
        logo_url="https://neworg.com/logo.png",
    )

    assert captured_body["name"] == "New Organization"
    assert captured_body["slug"] == "new-org"
    assert captured_body["website"] == "https://neworg.com"
    assert tenant["id"] == VALID_TENANT_ID
    assert tenant["slug"] == "new-org"


def test_tenants_create_validation():
    from nova_sdk import NovaClient

    client = NovaClient(api_key="test")
    with pytest.raises(NovaValidationError, match="name must be a non-empty string"):
        client.tenants.create(name="", slug="valid-slug")

    with pytest.raises(NovaValidationError, match="slug must be a non-empty string"):
        client.tenants.create(name="Valid Name", slug="")


def test_tenants_get_explicit_and_default_id(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == f"/api/v1/tenants/{VALID_TENANT_ID}/"
        return json_response(
            data={"id": VALID_TENANT_ID, "name": "Infimatrix", "slug": "infimatrix"}
        )

    # 1. With explicit tenant_id argument
    client = mock_client_factory(handler, api_key="test")
    t1 = client.tenants.get(VALID_TENANT_ID)
    assert t1["id"] == VALID_TENANT_ID

    # 2. With client-configured default tenant_id
    client_with_default = mock_client_factory(
        handler, api_key="test", tenant_id=VALID_TENANT_ID
    )
    t2 = client_with_default.tenants.get()
    assert t2["id"] == VALID_TENANT_ID


def test_tenants_get_not_found(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=404,
            message="Tenant not found.",
            error_code="NOT_FOUND",
        )

    client = mock_client_factory(handler, api_key="test")
    with pytest.raises(NovaNotFoundError):
        client.tenants.get(VALID_TENANT_ID)


def test_tenants_update(mock_client_factory):
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == f"/api/v1/tenants/{VALID_TENANT_ID}/"
        captured_body.update(json.loads(request.content.decode("utf-8")))
        return json_response(
            data={
                "id": VALID_TENANT_ID,
                "name": "Updated Org Name",
                "status": "ACTIVE",
            }
        )

    client = mock_client_factory(handler, api_key="test")
    updated = client.tenants.update(
        VALID_TENANT_ID,
        name="Updated Org Name",
    )
    assert captured_body == {"name": "Updated Org Name"}
    assert updated["name"] == "Updated Org Name"


def test_tenants_update_permission_denied(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=403,
            message="Only Tenant Admins can update or delete workspaces.",
            error_code="PERMISSION_DENIED",
        )

    client = mock_client_factory(handler, api_key="test")
    with pytest.raises(NovaPermissionError) as exc_info:
        client.tenants.update(VALID_TENANT_ID, name="Hacked Name")

    assert exc_info.value.status_code == 403


def test_tenants_delete(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == f"/api/v1/tenants/{VALID_TENANT_ID}/"
        return httpx.Response(status_code=204)

    client = mock_client_factory(handler, api_key="test")
    client.tenants.delete(VALID_TENANT_ID)


def test_tenants_memberships_list(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == f"/api/v1/tenants/{VALID_TENANT_ID}/members/"
        return json_response(
            data={
                "pagination": {
                    "count": 1,
                    "page": 1,
                    "total_pages": 1,
                    "page_size": 20,
                },
                "results": [
                    {
                        "id": VALID_MEMBER_ID,
                        "user_id": "99999999-9999-9999-9999-999999999999",
                        "user_email": "admin@infimatrix.com",
                        "role": Role.TENANT_ADMIN,
                        "status": "ACTIVE",
                    }
                ],
            }
        )

    client = mock_client_factory(handler, api_key="test")
    members = client.tenants.memberships.list(VALID_TENANT_ID)

    assert len(members) == 1
    assert members[0]["user_email"] == "admin@infimatrix.com"
    assert members[0]["role"] == "TENANT_ADMIN"


def test_tenants_memberships_add(mock_client_factory):
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == f"/api/v1/tenants/{VALID_TENANT_ID}/members/"
        captured_body.update(json.loads(request.content.decode("utf-8")))
        return json_response(
            status_code=201,
            data={
                "id": VALID_MEMBER_ID,
                "user_email": "newuser@infimatrix.com",
                "role": Role.CAMPAIGN_MANAGER,
                "status": "ACTIVE",
            },
        )

    client = mock_client_factory(handler, api_key="test")
    member = client.tenants.add_member(
        VALID_TENANT_ID,
        email="newuser@infimatrix.com",
        role=Role.CAMPAIGN_MANAGER,
    )

    assert captured_body == {
        "email": "newuser@infimatrix.com",
        "role": "CAMPAIGN_MANAGER",
        "status": "ACTIVE",
    }
    assert member["role"] == "CAMPAIGN_MANAGER"


def test_tenants_memberships_add_user_not_found_error(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=400,
            message="No registered user found with email 'unknown@example.com'.",
            error_code="VALIDATION_ERROR",
            data={
                "email": "No registered user found with email 'unknown@example.com'."
            },
        )

    client = mock_client_factory(handler, api_key="test")
    with pytest.raises(NovaValidationError) as exc_info:
        client.tenants.memberships.add(VALID_TENANT_ID, email="unknown@example.com")

    assert exc_info.value.status_code == 400


def test_tenants_memberships_get(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert (
            request.url.path
            == f"/api/v1/tenants/{VALID_TENANT_ID}/members/{VALID_MEMBER_ID}/"
        )
        return json_response(
            data={"id": VALID_MEMBER_ID, "user_email": "member@example.com"}
        )

    client = mock_client_factory(handler, api_key="test")
    res = client.tenants.get_member(VALID_MEMBER_ID, tenant_id=VALID_TENANT_ID)
    assert res["id"] == VALID_MEMBER_ID


def test_tenants_memberships_update(mock_client_factory):
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert (
            request.url.path
            == f"/api/v1/tenants/{VALID_TENANT_ID}/members/{VALID_MEMBER_ID}/"
        )
        captured_body.update(json.loads(request.content.decode("utf-8")))
        return json_response(
            data={
                "id": VALID_MEMBER_ID,
                "role": Role.SENDER,
                "status": "INACTIVE",
            }
        )

    client = mock_client_factory(handler, api_key="test")
    updated = client.tenants.update_member(
        VALID_MEMBER_ID,
        tenant_id=VALID_TENANT_ID,
        role=Role.SENDER,
        status="INACTIVE",
    )
    assert captured_body == {"role": "SENDER", "status": "INACTIVE"}
    assert updated["role"] == "SENDER"


def test_tenants_memberships_remove(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert (
            request.url.path
            == f"/api/v1/tenants/{VALID_TENANT_ID}/members/{VALID_MEMBER_ID}/"
        )
        return httpx.Response(status_code=204)

    client = mock_client_factory(handler, api_key="test")
    client.tenants.remove_member(VALID_MEMBER_ID, tenant_id=VALID_TENANT_ID)


def test_tenants_membership_missing_tenant_id():
    from nova_sdk import NovaClient

    client = NovaClient(api_key="test")
    with pytest.raises(NovaValidationError, match="tenant_id must be provided"):
        client.tenants.memberships.list()
