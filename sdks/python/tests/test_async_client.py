"""Tests for the asyncio client (AsyncNovaClient) and its generated resources."""

from __future__ import annotations

import asyncio
import inspect
import json

import httpx
import pytest
from helpers import json_response

from nova_sdk import NovaClient, schemas
from nova_sdk.aio import AsyncNovaClient
from nova_sdk.exceptions import (
    NovaConnectionError,
    NovaNotFoundError,
    NovaRateLimitError,
    NovaServerError,
)

TENANT = "11111111-1111-1111-1111-111111111111"


def run(coro):
    return asyncio.run(coro)


def test_async_request_returns_typed_models(async_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["authorization"] == "Bearer nova_key_test"
        assert request.headers["x-tenant-id"] == TENANT
        assert request.url.path == f"/api/v1/tenants/{TENANT}/"
        return json_response(data={"id": TENANT, "name": "Infimatrix"})

    async def main():
        async with async_client_factory(
            handler, api_key="nova_key_test", tenant_id=TENANT
        ) as c:
            return await c.tenants.get()

    tenant = run(main())
    assert isinstance(tenant, schemas.Tenant)
    assert tenant.name == "Infimatrix"


def test_async_error_mapping(async_client_factory):
    def handler(request):
        return json_response(status_code=404, message="gone", error_code="NOT_FOUND")

    async def main():
        client = async_client_factory(handler, api_key="k")
        await client.templates.get("missing")

    with pytest.raises(NovaNotFoundError) as exc:
        run(main())
    assert exc.value.correlation_id == "test-corr-12345"


def test_async_get_retries_transient_errors(async_client_factory):
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        if calls < 3:
            return json_response(status_code=503, message="down")
        return json_response(data={"status": "ok"})

    async def main():
        client = async_client_factory(
            handler, max_retries=3, retry_backoff_factor=0.001
        )
        return await client.health()

    assert run(main()) == {"status": "ok"}
    assert calls == 3


def test_async_post_is_never_retried(async_client_factory):
    calls = 0

    def handler(request):
        nonlocal calls
        calls += 1
        return json_response(status_code=503, message="down")

    async def main():
        client = async_client_factory(
            handler, max_retries=3, retry_backoff_factor=0.001
        )
        await client.emails.send(recipient_email="a@b.co", subject="hi")

    with pytest.raises(NovaServerError):
        run(main())
    assert calls == 1


def test_async_honours_retry_after_on_rate_limit(async_client_factory):
    def handler(request):
        return json_response(
            status_code=429, message="slow down", headers={"Retry-After": "3"}
        )

    async def main():
        client = async_client_factory(handler, max_retries=0)
        await client.templates.list()

    with pytest.raises(NovaRateLimitError) as exc:
        run(main())
    assert exc.value.retry_after == 3


def test_async_connection_failure(async_client_factory):
    def handler(request):
        raise httpx.ConnectError("refused", request=request)

    async def main():
        client = async_client_factory(
            handler, max_retries=1, retry_backoff_factor=0.001
        )
        await client.health()

    with pytest.raises(NovaConnectionError):
        run(main())


def test_async_pagination_helpers(async_client_factory):
    def handler(request):
        page = int(request.url.params.get("page", 1))
        return json_response(
            data={
                "pagination": {
                    "count": 4,
                    "next": "x" if page < 2 else None,
                    "page": page,
                    "total_pages": 2,
                    "page_size": 2,
                },
                "results": [{"id": f"{page}-a"}, {"id": f"{page}-b"}],
            }
        )

    async def main():
        client = async_client_factory(handler, api_key="k")
        return [i["id"] async for i in client.iter_items(client.templates.list)]

    assert run(main()) == ["1-a", "1-b", "2-a", "2-b"]


def test_async_multipart_upload(async_client_factory):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["content-type"].startswith("multipart/form-data")
        assert b'filename="a.png"' in request.content
        return json_response(status_code=201, data={"id": "f1", "name": "a.png"})

    async def main():
        client = async_client_factory(handler, api_key="k")
        return await client.assets.files.upload(b"png", filename="a.png")

    assert run(main()).name == "a.png"


def test_async_sub_resource_shortcuts(async_client_factory):
    def handler(request):
        assert request.url.path == f"/api/v1/tenants/{TENANT}/members/"
        return json_response(data={"pagination": {"count": 0}, "results": []})

    async def main():
        client = async_client_factory(handler, api_key="k", tenant_id=TENANT)
        return await client.tenants.list_members()

    assert len(run(main())) == 0


def test_async_login_sets_token(async_client_factory):
    def handler(request):
        assert json.loads(request.content)["email"] == "a@b.co"
        return json_response(
            data={"access": "jwt", "refresh": "r", "user": {}, "tenants": []}
        )

    async def main():
        client = async_client_factory(handler)
        result = await client.auth.login(
            email="a@b.co", password="pw", set_current_token=True
        )
        return client, result

    client, result = run(main())
    assert result.access == "jwt"
    assert client.config.access_token == "jwt"


def test_async_repr_redacts_secrets():
    client = AsyncNovaClient(api_key="nova_key_supersecretvalue123")
    assert "supersecretvalue" not in repr(client)


def test_async_transport_close_respects_injected_client():
    async def main():
        http = httpx.AsyncClient()
        client = AsyncNovaClient(api_key="k", _http_client=http)
        await client.aclose()
        assert not http.is_closed
        await http.aclose()

        owned = AsyncNovaClient(api_key="k")
        await owned.aclose()
        assert owned.transport.is_closed

    run(main())


# -- parity -------------------------------------------------------------------
def _public_methods(resource):
    return {
        name
        for name, member in inspect.getmembers(type(resource), inspect.isfunction)
        if not name.startswith("_")
    }


def test_async_client_mirrors_sync_resource_surface():
    sync = NovaClient(api_key="k")
    aio = AsyncNovaClient(api_key="k")
    resources = [
        name
        for name, value in vars(sync).items()
        if not name.startswith("_") and hasattr(value, "_transport")
    ]
    assert resources, "expected resource attributes on the sync client"
    for name in resources:
        sync_res, aio_res = getattr(sync, name), getattr(aio, name)
        assert _public_methods(sync_res) == _public_methods(aio_res), name
        for method in _public_methods(aio_res):
            fn = getattr(type(aio_res), method)
            assert inspect.iscoroutinefunction(fn), f"{name}.{method} must be async"
            sync_params = inspect.signature(getattr(type(sync_res), method)).parameters
            aio_params = inspect.signature(fn).parameters
            assert list(sync_params) == list(aio_params), f"{name}.{method} signature"
        # nested resources (api_keys, groups, memberships, ...)
        for sub_name, sub in vars(sync_res).items():
            if hasattr(sub, "_transport") and not sub_name.startswith("_"):
                assert _public_methods(sub) == _public_methods(
                    getattr(aio_res, sub_name)
                )
