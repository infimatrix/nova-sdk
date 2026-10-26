"""Tests for TemplatesResource client."""

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
from nova_sdk.models import TemplateStatus

VALID_TEMPLATE_ID = "44444444-4444-4444-4444-444444444444"
TENANT_ALPHA = "11111111-1111-1111-1111-111111111111"
TENANT_BETA = "22222222-2222-2222-2222-222222222222"


def test_templates_list_defaults(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/templates/"
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
                        "id": VALID_TEMPLATE_ID,
                        "name": "Welcome Email",
                        "slug": "welcome-email",
                        "subject": "Welcome to Nova, {{ name }}!",
                        "status": TemplateStatus.ACTIVE,
                    },
                    {
                        "id": "55555555-5555-5555-5555-555555555555",
                        "name": "Password Reset",
                        "slug": "password-reset",
                        "subject": "Reset your password",
                        "status": TemplateStatus.DRAFT,
                    },
                ],
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    templates = client.templates.list()

    assert len(templates) == 2
    assert templates[0]["name"] == "Welcome Email"
    assert templates[1]["slug"] == "password-reset"
    assert templates.pagination.count == 2
    # Verify sequence iteration
    names = [t["name"] for t in templates]
    assert names == ["Welcome Email", "Password Reset"]


def test_templates_list_with_query_params(mock_client_factory):
    captured_params: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v1/templates/"
        captured_params.update(dict(request.url.params))
        return json_response(data={"results": [], "pagination": {"count": 0}})

    client = mock_client_factory(handler, api_key="nova_key_test")
    client.templates.list(
        status=TemplateStatus.ACTIVE,
        search="welcome",
        ordering="-created_at",
        page=2,
        page_size=10,
    )

    assert captured_params["status"] == "ACTIVE"
    assert captured_params["search"] == "welcome"
    assert captured_params["ordering"] == "-created_at"
    assert captured_params["page"] == "2"
    assert captured_params["page_size"] == "10"


def test_templates_get_success(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == f"/api/v1/templates/{VALID_TEMPLATE_ID}/"
        return json_response(
            data={
                "id": VALID_TEMPLATE_ID,
                "name": "Welcome Email",
                "slug": "welcome-email",
                "subject": "Welcome to Nova!",
                "html_content": "<h1>Welcome</h1>",
                "text_content": "Welcome",
                "status": "ACTIVE",
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    tpl = client.templates.get(VALID_TEMPLATE_ID)
    assert tpl["id"] == VALID_TEMPLATE_ID
    assert tpl["name"] == "Welcome Email"


def test_templates_get_validation_error(mock_client_factory):
    client = mock_client_factory(lambda r: httpx.Response(200))
    with pytest.raises(
        NovaValidationError, match="template_id must be a non-empty string"
    ):
        client.templates.get("")


def test_templates_get_not_found(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=404,
            message="Template not found.",
            error_code="NOT_FOUND",
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    with pytest.raises(NovaNotFoundError):
        client.templates.get("nonexistent-template")


def test_templates_create_success(mock_client_factory):
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/templates/"
        captured_body.update(json.loads(request.content.decode("utf-8")))
        return json_response(
            status_code=201,
            data={
                "id": VALID_TEMPLATE_ID,
                "name": "Onboarding Welcome",
                "slug": "onboarding-welcome",
                "subject": "Welcome, {{ userName }}!",
                "html_content": "<p>Hello {{ userName }}</p>",
                "text_content": "Hello {{ userName }}",
                "status": "ACTIVE",
                "placeholders": [
                    {
                        "name": "userName",
                        "default_value": "Valued User",
                        "is_required": True,
                    }
                ],
            },
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    tpl = client.templates.create(
        name="Onboarding Welcome",
        subject="Welcome, {{ userName }}!",
        html_content="<p>Hello {{ userName }}</p>",
        text_content="Hello {{ userName }}",
        status=TemplateStatus.ACTIVE,
        placeholders=[
            {"name": "userName", "default_value": "Valued User", "is_required": True}
        ],
    )

    assert captured_body["name"] == "Onboarding Welcome"
    assert captured_body["subject"] == "Welcome, {{ userName }}!"
    assert captured_body["status"] == "ACTIVE"
    assert len(captured_body["placeholders"]) == 1
    assert tpl["id"] == VALID_TEMPLATE_ID
    assert tpl["slug"] == "onboarding-welcome"


def test_templates_create_validation_error(mock_client_factory):
    client = mock_client_factory(lambda r: httpx.Response(200))
    with pytest.raises(NovaValidationError, match="name must be a non-empty string"):
        client.templates.create(name="")


def test_templates_update_success(mock_client_factory):
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        assert request.url.path == f"/api/v1/templates/{VALID_TEMPLATE_ID}/"
        captured_body.update(json.loads(request.content.decode("utf-8")))
        return json_response(
            data={
                "id": VALID_TEMPLATE_ID,
                "name": "Renamed Template",
                "subject": "New Subject",
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    updated = client.templates.update(
        VALID_TEMPLATE_ID,
        name="Renamed Template",
        subject="New Subject",
    )

    assert captured_body == {"name": "Renamed Template", "subject": "New Subject"}
    assert updated["name"] == "Renamed Template"


def test_templates_activate_and_archive_shortcuts(mock_client_factory):
    requests_sent: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "PATCH"
        body = json.loads(request.content.decode("utf-8"))
        requests_sent.append(body)
        return json_response(data={"id": VALID_TEMPLATE_ID, "status": body["status"]})

    client = mock_client_factory(handler, api_key="nova_key_test")
    client.templates.activate(VALID_TEMPLATE_ID)
    client.templates.archive(VALID_TEMPLATE_ID)

    assert len(requests_sent) == 2
    assert requests_sent[0] == {"status": "ACTIVE"}
    assert requests_sent[1] == {"status": "ARCHIVED"}


def test_templates_delete_success(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == f"/api/v1/templates/{VALID_TEMPLATE_ID}/"
        return httpx.Response(status_code=204)

    client = mock_client_factory(handler, api_key="nova_key_test")
    client.templates.delete(VALID_TEMPLATE_ID)


def test_templates_render_success(mock_client_factory):
    captured_body: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == f"/api/v1/templates/{VALID_TEMPLATE_ID}/render/"
        captured_body.update(json.loads(request.content.decode("utf-8")))
        return json_response(
            data={
                "subject": "Welcome, Swaraj!",
                "html_content": "<p>Hello Swaraj</p>",
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    result = client.templates.render(
        VALID_TEMPLATE_ID,
        variables={"userName": "Swaraj"},
    )

    assert captured_body == {"variables": {"userName": "Swaraj"}}
    assert result["subject"] == "Welcome, Swaraj!"
    assert result["html_content"] == "<p>Hello Swaraj</p>"


def test_templates_tenant_isolation(mock_client_factory):
    captured_tenant: dict[str, str | None] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_tenant["header"] = request.headers.get("X-Tenant-ID")
        return json_response(data={"results": [], "pagination": {"count": 0}})

    client = mock_client_factory(
        handler, api_key="nova_key_test", tenant_id=TENANT_ALPHA
    )

    # 1. Default tenant header
    client.templates.list()
    assert captured_tenant["header"] == TENANT_ALPHA

    # 2. Per-request explicit tenant override without mutating client default
    client.templates.list(tenant_id=TENANT_BETA)
    assert captured_tenant["header"] == TENANT_BETA
    assert client.tenant_id == TENANT_ALPHA


def test_templates_permission_denied(mock_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            status_code=403,
            message="You do not have permission to access templates in this tenant.",
            error_code="PERMISSION_DENIED",
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    with pytest.raises(NovaPermissionError) as exc_info:
        client.templates.list()

    assert exc_info.value.status_code == 403
