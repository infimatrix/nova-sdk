"""Tests for ContactsResource and ContactGroupsResource clients."""

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
from nova_sdk.models import ContactStatus

VALID_CONTACT_ID = "66666666-6666-6666-6666-666666666666"
VALID_GROUP_ID = "77777777-7777-7777-7777-777777777777"
TENANT_ALPHA = "11111111-1111-1111-1111-111111111111"
TENANT_BETA = "22222222-2222-2222-2222-222222222222"


def test_contacts_list_defaults(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/contacts/"
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
                        "id": VALID_CONTACT_ID,
                        "email": "alice@example.com",
                        "first_name": "Alice",
                        "last_name": "Smith",
                        "status": ContactStatus.SUBSCRIBED,
                    },
                    {
                        "id": "88888888-8888-8888-8888-888888888888",
                        "email": "bob@example.com",
                        "first_name": "Bob",
                        "last_name": "Jones",
                        "status": ContactStatus.UNSUBSCRIBED,
                    },
                ],
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    contacts = client.contacts.list()

    assert len(contacts) == 2
    assert contacts[0]["email"] == "alice@example.com"
    assert contacts[1]["status"] == "UNSUBSCRIBED"
    assert contacts.pagination.count == 2
    emails = [c["email"] for c in contacts]
    assert emails == ["alice@example.com", "bob@example.com"]


def test_contacts_list_with_query_params(mock_client_factory):
    captured_params: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/contacts/"
        captured_params.update(dict(request.url.params))
        return json_response(data={"results": [], "pagination": {"count": 0}})

    client = mock_client_factory(handler, api_key="nova_key_test")
    client.contacts.list(
        timezone="America/New_York",
        search="alice",
        ordering="-created_at",
        page=3,
        page_size=25,
    )

    assert "status" not in captured_params
    assert captured_params["timezone"] == "America/New_York"
    assert captured_params["search"] == "alice"
    assert captured_params["ordering"] == "-created_at"
    assert captured_params["page"] == "3"
    assert captured_params["page_size"] == "25"


def test_contacts_list_rejects_status_kwarg(mock_client_factory):
    client = mock_client_factory(lambda r: httpx.Response(200))
    with pytest.raises(
        NovaValidationError,
        match="Status filtering on contacts is not supported by the Nova backend API",
    ):
        client.contacts.list(status=ContactStatus.SUBSCRIBED)


def test_contacts_list_rejects_status_in_params(mock_client_factory):
    client = mock_client_factory(lambda r: httpx.Response(200))
    with pytest.raises(
        NovaValidationError,
        match="Status filtering on contacts is not supported by the Nova backend API",
    ):
        client.contacts.list(params={"status": "SUBSCRIBED"})


def test_contacts_get_success(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == f"/api/v1/contacts/{VALID_CONTACT_ID}/"
        return json_response(
            data={
                "id": VALID_CONTACT_ID,
                "email": "alice@example.com",
                "first_name": "Alice",
                "last_name": "Smith",
                "status": "SUBSCRIBED",
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    contact = client.contacts.get(VALID_CONTACT_ID)
    assert contact["id"] == VALID_CONTACT_ID
    assert contact["email"] == "alice@example.com"


def test_contacts_get_validation_error(mock_client_factory):
    client = mock_client_factory(lambda r: httpx.Response(200))
    with pytest.raises(
        NovaValidationError, match="contact_id must be a non-empty string"
    ):
        client.contacts.get("")


def test_contacts_get_not_found(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=404,
            message="Contact not found.",
            error_code="NOT_FOUND",
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    with pytest.raises(NovaNotFoundError):
        client.contacts.get("nonexistent-contact")


def test_contacts_create_success(mock_client_factory):
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/contacts/"
        captured_body.update(json.loads(request.content.decode("utf-8")))
        return json_response(
            status_code=201,
            data={
                "id": VALID_CONTACT_ID,
                "email": "charlie@example.com",
                "first_name": "Charlie",
                "last_name": "Brown",
                "phone_number": "9876543210",
                "country_code": "+91",
                "status": "SUBSCRIBED",
            },
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    contact = client.contacts.create(
        email="Charlie@Example.com",
        first_name="Charlie",
        last_name="Brown",
        phone_number="9876543210",
        country_code="+91",
        status=ContactStatus.SUBSCRIBED,
        metadata={"source": "website_signup"},
    )

    assert captured_body["email"] == "charlie@example.com"
    assert captured_body["first_name"] == "Charlie"
    assert captured_body["phone_number"] == "9876543210"
    assert captured_body["metadata"] == {"source": "website_signup"}
    assert contact["id"] == VALID_CONTACT_ID


def test_contacts_create_validation_error(mock_client_factory):
    client = mock_client_factory(lambda r: httpx.Response(200))
    with pytest.raises(NovaValidationError, match="email must be a non-empty string"):
        client.contacts.create(email="")


def test_contacts_update_success(mock_client_factory):
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == f"/api/v1/contacts/{VALID_CONTACT_ID}/"
        captured_body.update(json.loads(request.content.decode("utf-8")))
        return json_response(
            data={
                "id": VALID_CONTACT_ID,
                "first_name": "Alice M.",
                "status": "UNSUBSCRIBED",
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    updated = client.contacts.update(
        VALID_CONTACT_ID,
        first_name="Alice M.",
        status=ContactStatus.UNSUBSCRIBED,
    )

    assert captured_body == {"first_name": "Alice M.", "status": "UNSUBSCRIBED"}
    assert updated["status"] == "UNSUBSCRIBED"


def test_contacts_delete_success(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == f"/api/v1/contacts/{VALID_CONTACT_ID}/"
        return httpx.Response(status_code=204)

    client = mock_client_factory(handler, api_key="nova_key_test")
    client.contacts.delete(VALID_CONTACT_ID)


def test_contacts_bulk_delete_success(mock_client_factory):
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/contacts/bulk-delete/"
        captured_body.update(json.loads(request.content.decode("utf-8")))
        return json_response(data={"success": True, "deleted_count": 2})

    client = mock_client_factory(handler, api_key="nova_key_test")
    result = client.contacts.bulk_delete(
        [VALID_CONTACT_ID, "88888888-8888-8888-8888-888888888888"]
    )

    assert captured_body == {
        "contact_ids": [VALID_CONTACT_ID, "88888888-8888-8888-8888-888888888888"]
    }
    assert result["success"] is True
    assert result["deleted_count"] == 2


def test_contacts_bulk_delete_validation_error(mock_client_factory):
    client = mock_client_factory(lambda r: httpx.Response(200))
    with pytest.raises(
        NovaValidationError, match="contact_ids must be a non-empty list of IDs"
    ):
        client.contacts.bulk_delete([])


def test_contacts_activity(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == f"/api/v1/contacts/{VALID_CONTACT_ID}/activity/"
        return json_response(
            data=[
                {
                    "id": "99999999-9999-9999-9999-999999999999",
                    "title": "Welcome Email",
                    "subject": "Welcome!",
                    "status": "DELIVERED",
                    "timestamp": "2026-10-24T12:00:00Z",
                }
            ]
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    timeline = client.contacts.activity(VALID_CONTACT_ID)

    assert len(timeline) == 1
    assert timeline[0]["status"] == "DELIVERED"
    assert timeline[0]["subject"] == "Welcome!"


def test_contacts_sample_template(mock_client_factory):
    csv_content = "user_id,username,first_name,last_name,email,country_code,mobile_number,timezone\nUSR001,johnd,John,Doe,john@example.com,+91,9876543210,EST\n"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/contacts/sample-template/"
        return httpx.Response(
            status_code=200,
            text=csv_content,
            headers={"Content-Type": "text/csv; charset=utf-8"},
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    content = client.contacts.sample_template()
    assert "user_id,username,first_name" in content
    assert "john@example.com" in content


def test_contacts_bulk_upload_bytes(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/contacts/bulk-upload/"
        assert "multipart/form-data" in request.headers.get("Content-Type", "")
        return json_response(
            data={
                "message": "Successfully imported 2 contacts.",
                "created_count": 2,
                "errors": [],
                "contacts": [{"email": "user1@test.com"}, {"email": "user2@test.com"}],
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    csv_bytes = b"email,first_name\nuser1@test.com,User1\nuser2@test.com,User2\n"
    res = client.contacts.bulk_upload(csv_bytes, filename="import.csv")

    assert res["created_count"] == 2
    assert len(res["contacts"]) == 2


def test_contacts_bulk_upload_stream_rewound(mock_client_factory):
    import io

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/contacts/bulk-upload/"
        return json_response(
            data={
                "message": "Successfully imported 1 contact.",
                "created_count": 1,
                "errors": [],
                "contacts": [{"email": "stream@example.com"}],
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    stream = io.BytesIO(b"email,first_name\nstream@example.com,Stream\n")
    res = client.contacts.bulk_upload(stream, filename="stream.csv")

    assert res["created_count"] == 1
    assert res["contacts"][0]["email"] == "stream@example.com"


def test_contacts_bulk_upload_eof_stream_raises_validation_error(mock_client_factory):
    import io

    client = mock_client_factory(lambda r: httpx.Response(200))
    stream = io.BytesIO(b"email,first_name\neof@example.com,EOF\n")
    stream.read()  # Advance file pointer to end of stream (EOF)

    with pytest.raises(
        NovaValidationError,
        match="file content is empty. If passing an open file stream, ensure it is rewound",
    ):
        client.contacts.bulk_upload(stream)


def test_contact_groups_crud(mock_client_factory):
    captured_data: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "GET" and path == "/api/v1/contacts/groups/":
            return json_response(
                data={
                    "pagination": {
                        "count": 1,
                        "page": 1,
                        "total_pages": 1,
                        "page_size": 20,
                    },
                    "results": [{"id": VALID_GROUP_ID, "name": "VIP Customers"}],
                }
            )
        elif request.method == "POST" and path == "/api/v1/contacts/groups/":
            captured_data["create"] = json.loads(request.content.decode("utf-8"))
            return json_response(
                status_code=201, data={"id": VALID_GROUP_ID, "name": "VIP Customers"}
            )
        elif (
            request.method == "GET"
            and path == f"/api/v1/contacts/groups/{VALID_GROUP_ID}/"
        ):
            return json_response(data={"id": VALID_GROUP_ID, "name": "VIP Customers"})
        elif (
            request.method == "PATCH"
            and path == f"/api/v1/contacts/groups/{VALID_GROUP_ID}/"
        ):
            captured_data["patch"] = json.loads(request.content.decode("utf-8"))
            return json_response(data={"id": VALID_GROUP_ID, "name": "Updated VIP"})
        elif (
            request.method == "DELETE"
            and path == f"/api/v1/contacts/groups/{VALID_GROUP_ID}/"
        ):
            return httpx.Response(status_code=204)
        return httpx.Response(status_code=404)

    client = mock_client_factory(handler, api_key="nova_key_test")

    # List
    groups = client.contacts.list_groups()
    assert len(groups) == 1
    assert groups[0]["name"] == "VIP Customers"

    # Create
    new_group = client.contacts.create_group(
        name="VIP Customers", description="Top tier subscribers"
    )
    assert new_group["id"] == VALID_GROUP_ID
    assert captured_data["create"]["name"] == "VIP Customers"

    # Get
    group = client.contacts.get_group(VALID_GROUP_ID)
    assert group["name"] == "VIP Customers"

    # Update
    updated = client.contacts.update_group(VALID_GROUP_ID, name="Updated VIP")
    assert updated["name"] == "Updated VIP"
    assert captured_data["patch"]["name"] == "Updated VIP"

    # Delete
    client.contacts.delete_group(VALID_GROUP_ID)


def test_contacts_tenant_isolation(mock_client_factory):
    captured_tenant: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_tenant["header"] = request.headers.get("X-Tenant-ID")
        return json_response(data={"results": [], "pagination": {"count": 0}})

    client = mock_client_factory(
        handler, api_key="nova_key_test", tenant_id=TENANT_ALPHA
    )

    # 1. Default tenant
    client.contacts.list()
    assert captured_tenant["header"] == TENANT_ALPHA

    # 2. Per-request explicit tenant override
    client.contacts.list(tenant_id=TENANT_BETA)
    assert captured_tenant["header"] == TENANT_BETA
    assert client.tenant_id == TENANT_ALPHA


def test_contacts_permission_denied(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=403,
            message="You do not have permission to view contacts in this tenant.",
            error_code="PERMISSION_DENIED",
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    with pytest.raises(NovaPermissionError) as exc_info:
        client.contacts.list()

    assert exc_info.value.status_code == 403
