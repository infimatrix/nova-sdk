"""Property tests for invariants the documentation states (docs/conventions.md, authentication.md).

Every property below cites its source; none asserts a behaviour the docs do not promise. Failures print a
reproduction blob (``@reproduce_failure``) and can be replayed with ``pytest --hypothesis-seed=<n>``.
"""

from __future__ import annotations

import json
from urllib.parse import parse_qsl, unquote

import httpx
import pytest
from helpers import json_response
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from nova_sdk import NovaClient
from nova_sdk.exceptions import NovaError, NovaValidationError
from nova_sdk.pagination import iter_items

PROPS = settings(
    max_examples=200,
    deadline=None,
    print_blob=True,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
PREFIX = "/api/v1/templates/"


def _client(handler, **kwargs) -> NovaClient:
    return NovaClient(
        base_url="http://nova.test",
        api_key="nova_key_x",
        _http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        **kwargs,
    )


@PROPS
@given(st.text(max_size=40))
def test_path_id_never_adds_segments_or_query(identifier: str):
    """conventions.md "Path ids": a hostile id cannot add path segments or query strings."""
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return json_response(data={"id": "x", "name": "n"})

    client = _client(handler)
    stripped = identifier.strip()
    if not stripped or stripped in (".", ".."):
        with pytest.raises(NovaValidationError):
            client.templates.get(identifier)
        assert seen == []
        return

    client.templates.get(identifier)
    assert len(seen) == 1
    raw = seen[0].url.raw_path.decode()
    assert "?" not in raw and "#" not in raw
    assert raw.startswith(PREFIX) and raw.endswith("/")
    segment = raw[len(PREFIX) : -1]
    assert "/" not in segment
    assert segment not in (".", "..")
    assert unquote(segment) == stripped


@PROPS
@given(st.text(min_size=1, max_size=40).filter(lambda s: s.strip() == s and s != ""))
def test_search_value_round_trips_to_the_server(value: str):
    """RFC 3986 percent-encoding: the server decodes exactly the value the caller passed."""
    seen: list[list[tuple[str, str]]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(parse_qsl(request.url.query.decode(), keep_blank_values=True))
        payload = {
            "success": True,
            "message": "ok",
            "data": {"success": True, "pagination": {}, "results": []},
        }
        return httpx.Response(
            200, json=payload, headers={"Content-Type": "application/json"}
        )

    _client(handler).templates.list(search=value)
    assert len(seen) == 1
    assert [v for k, v in seen[0] if k == "search"] == [value]


@PROPS
@given(
    host=st.from_regex(r"[a-z][a-z0-9]{0,10}(\.[a-z]{2,6}){0,2}", fullmatch=True),
    suffix=st.sampled_from(["", "/", "/api", "/api/", "/api/v1", "/api/v1/"]),
    port=st.one_of(st.none(), st.integers(1, 65535)),
)
def test_base_url_normalisation(host: str, suffix: str, port):
    """conventions.md "Base URL": strip trailing '/', '/api' or '/api/v1'; result is stable."""
    origin = f"http://{host}" + (f":{port}" if port else "")
    first = NovaClient(base_url=origin + suffix, api_key="k").config.base_url
    assert first == origin
    assert NovaClient(base_url=first, api_key="k").config.base_url == first


@PROPS
@given(
    key=st.text(
        alphabet=st.characters(
            min_codepoint=48, max_codepoint=122, whitelist_categories=("L", "N")
        ),
        min_size=8,
        max_size=40,
    ),
    status=st.sampled_from([400, 401, 403, 404, 409, 418, 429, 500, 502, 503]),
)
def test_api_key_never_appears_in_errors_or_reprs(key: str, status: int):
    """authentication.md "Handling secrets": credentials never appear in messages, repr or logs."""
    secret = f"nova_key_{key}"

    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(status_code=status, message="failure", error_code="X")

    client = NovaClient(
        base_url="http://nova.test",
        api_key=secret,
        max_retries=0,
        _http_client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(NovaError) as info:
        client.templates.create(name="n")
    for text in (
        str(info.value),
        repr(info.value),
        repr(client),
        repr(client.config),
        str(client.config),
    ):
        assert secret not in text


@PROPS
@given(st.lists(st.integers(0, 5), min_size=1, max_size=6), st.integers(1, 50))
def test_iteration_visits_every_item_once_in_order(sizes: list[int], page_size: int):
    """conventions.md "Pagination": helpers iterate all pages; nothing skipped or duplicated."""
    total = len(sizes)
    pages = []
    n = 0
    for size in sizes:
        pages.append([f"id-{n + i}" for i in range(size)])
        n += size
    requested: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        page = int(dict(parse_qsl(request.url.query.decode())).get("page", "1"))
        requested.append(page)
        body = {
            "success": True,
            "message": "ok",
            "data": {
                "success": True,
                "pagination": {
                    "count": n,
                    "next": f"http://x/?page={page + 1}" if page < total else None,
                    "previous": None,
                    "page": page,
                    "total_pages": total,
                    "page_size": page_size,
                },
                "results": [{"id": i, "name": i} for i in pages[page - 1]],
            },
        }
        return httpx.Response(
            200, content=json.dumps(body), headers={"Content-Type": "application/json"}
        )

    items = [
        t.id for t in iter_items(_client(handler).templates.list, page_size=page_size)
    ]
    assert items == [i for p in pages for i in p]
    assert requested == list(range(1, total + 1))
