"""Structural checks of the committed contract snapshot (no backend required)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from openapi_spec_validator import validate

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "openapi" / "nova-api.yaml"
METHODS = ("get", "post", "put", "patch", "delete")
PUBLIC_PREFIXES = (
    "/api/v1/health",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
)


@pytest.fixture(scope="module")
def spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text())


def operations(spec):
    for path, item in spec["paths"].items():
        for method in METHODS:
            if method in item:
                yield method, path, item[method]


def test_snapshot_is_valid_openapi_3(spec):
    validate(spec)
    assert spec["openapi"].startswith("3.")


def test_success_responses_use_the_envelope(spec):
    for method, path, op in operations(spec):
        for code, resp in op["responses"].items():
            schema = (
                (resp.get("content") or {}).get("application/json", {}).get("schema")
            )
            if str(code).startswith("2") and schema is not None:
                name = schema["$ref"].rsplit("/", 1)[-1] if "$ref" in schema else None
                envelope = spec["components"]["schemas"][name] if name else schema
                assert {"success", "data", "meta"} <= set(envelope["properties"]), (
                    method,
                    path,
                )


def test_authenticated_operations_declare_auth_and_tenant(spec):
    for method, path, op in operations(spec):
        names = {p["name"] for p in op.get("parameters", [])}
        if path.startswith(PUBLIC_PREFIXES):
            assert op.get("security") == [], (method, path)
            assert "X-Tenant-ID" not in names, (method, path)
        else:
            assert op.get("security"), (method, path)
            assert {"401", "403"} <= set(op["responses"]), (method, path)
            assert "X-Tenant-ID" in names, (method, path)


def test_paginated_operations_expose_page_parameters(spec):
    for method, path, op in operations(spec):
        schema = (
            op["responses"]
            .get("200", {})
            .get("content", {})
            .get("application/json", {})
            .get("schema", {})
        )
        if schema.get("$ref", "").rsplit("/", 1)[-1].startswith("Paginated"):
            names = {p["name"] for p in op.get("parameters", [])}
            assert {"page", "page_size"} <= names, (method, path)


def test_error_envelope_is_defined(spec):
    schemas = spec["components"]["schemas"]
    assert {"ErrorEnvelope", "ErrorBody", "ResponseMeta", "PaginationInfo"} <= set(
        schemas
    )
    assert {"success", "message", "error", "meta"} <= set(
        schemas["ErrorEnvelope"]["properties"]
    )


def test_csv_exports_are_documented_as_csv(spec):
    for path in ("/api/v1/emails/logs/export/", "/api/v1/contacts/sample-template/"):
        assert "text/csv" in spec["paths"][path]["get"]["responses"]["200"]["content"]
