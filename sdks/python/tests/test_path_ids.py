"""Path identifiers are URL-encoded so they can never alter the request path."""

from __future__ import annotations

import asyncio

import httpx
import pytest
from helpers import json_response

from nova_sdk.exceptions import NovaValidationError

HOSTILE = "abc/../tenants?x=1#frag"


def _capture(seen):
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url.raw_path.decode())
        return json_response(data={"id": "x"})

    return handler


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.templates.get(HOSTILE),
        lambda c: c.contacts.get(HOSTILE),
        lambda c: c.contacts.groups.get(HOSTILE),
        lambda c: c.webhooks.get(HOSTILE),
        lambda c: c.providers.get(HOSTILE),
        lambda c: c.campaigns.get(HOSTILE),
        lambda c: c.audit.get(HOSTILE),
        lambda c: c.emails.get_log(HOSTILE),
        lambda c: c.assets.files.get(HOSTILE),
        lambda c: c.assets.folders.get(HOSTILE),
    ],
)
def test_hostile_ids_stay_inside_their_path_segment(mock_client_factory, call):
    seen: list[str] = []
    call(mock_client_factory(_capture(seen), api_key="k"))
    path = seen[0]
    assert "%2F..%2F" in path
    assert "?" not in path and "#" not in path
    assert path.count("/") == path.replace("%2F", "").count("/")  # no extra segments


def test_blank_ids_are_rejected(mock_client_factory):
    client = mock_client_factory(_capture([]), api_key="k")
    with pytest.raises(NovaValidationError):
        client.templates.get("   ")


def test_async_ids_are_encoded_too(async_client_factory):
    seen: list[str] = []

    async def main():
        client = async_client_factory(_capture(seen), api_key="k")
        await client.templates.get(HOSTILE)

    asyncio.run(main())
    assert "%2F..%2F" in seen[0]
