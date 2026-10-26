"""Tests for generated typed models and the dict-compatible NovaModel base."""

from __future__ import annotations

import pytest
from helpers import json_response

from nova_sdk import schemas
from nova_sdk._model_base import NovaModel, parse_model

TENANT = {
    "id": "11111111-1111-1111-1111-111111111111",
    "name": "Infimatrix",
    "slug": "infimatrix",
    "status": "ACTIVE",
    "is_active": True,
    "future_field": {"added": "later"},
}


def test_attribute_and_mapping_access():
    tenant = schemas.Tenant.from_dict(TENANT)
    assert tenant.name == "Infimatrix"
    assert tenant["name"] == "Infimatrix"
    assert tenant.get("slug") == "infimatrix"
    assert tenant.is_active is True
    assert "id" in tenant
    assert len(tenant) == len(TENANT)
    assert dict(tenant) == TENANT


def test_unknown_fields_are_preserved_in_raw():
    tenant = schemas.Tenant.from_dict(TENANT)
    assert tenant.raw["future_field"] == {"added": "later"}
    assert tenant.to_dict() == TENANT
    assert tenant.to_dict() is not tenant.raw


def test_missing_fields_default_to_none():
    tenant = schemas.Tenant.from_dict({"id": "x"})
    assert tenant.name is None
    assert tenant.raw == {"id": "x"}


def test_equality_with_dicts_and_models():
    tenant = schemas.Tenant.from_dict(TENANT)
    assert tenant == TENANT
    assert tenant == schemas.Tenant.from_dict(dict(TENANT))
    assert tenant != {"id": "other"}
    assert tenant != 5


def test_models_are_unhashable_like_dicts():
    with pytest.raises(TypeError):
        hash(schemas.Tenant.from_dict(TENANT))


def test_nested_models_are_parsed():
    user = schemas.UserMe.from_dict(
        {
            "id": "u1",
            "email": "a@example.com",
            "tenants": [{"id": "t1", "role": "TENANT_ADMIN"}],
            "current_tenant": {"id": "t1", "name": "Acme"},
        }
    )
    assert isinstance(user.tenants[0], NovaModel)
    assert user.tenants[0].role == "TENANT_ADMIN"
    assert isinstance(user.current_tenant, NovaModel)
    assert user.current_tenant.name == "Acme"


def test_from_dict_rejects_non_objects():
    with pytest.raises(TypeError):
        schemas.Tenant.from_dict("not-an-object")


def test_from_dict_is_idempotent():
    tenant = schemas.Tenant.from_dict(TENANT)
    assert schemas.Tenant.from_dict(tenant) is tenant


def test_parse_model_passes_through_non_mappings():
    assert parse_model(schemas.Tenant, None) is None
    assert parse_model(schemas.Tenant, "csv,text") == "csv,text"


def test_resource_methods_return_typed_models(mock_client_factory):
    def handler(request):
        return json_response(data=TENANT)

    client = mock_client_factory(handler, api_key="nova_key_test")
    tenant = client.tenants.get("11111111-1111-1111-1111-111111111111")
    assert isinstance(tenant, schemas.Tenant)
    assert tenant.slug == "infimatrix"


def test_paginated_lists_hold_typed_items(mock_client_factory):
    def handler(request):
        return json_response(
            data={
                "pagination": {
                    "count": 1,
                    "page": 1,
                    "total_pages": 1,
                    "page_size": 20,
                },
                "results": [TENANT],
            }
        )

    client = mock_client_factory(handler, api_key="nova_key_test")
    page = client.tenants.list()
    assert isinstance(page[0], schemas.Tenant)
    assert page.pagination.count == 1
    assert page.has_next is False
