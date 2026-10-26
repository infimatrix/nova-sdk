"""Tests for pagination helpers."""

from __future__ import annotations

import pytest
from helpers import json_response

from nova_sdk import iter_items, iter_pages
from nova_sdk.exceptions import NovaValidationError


def _paged_handler(total_pages: int, seen: list[int]):
    def handler(request):
        page = int(request.url.params.get("page", 1))
        seen.append(page)
        return json_response(
            data={
                "pagination": {
                    "count": total_pages * 2,
                    "next": f"http://x/?page={page + 1}"
                    if page < total_pages
                    else None,
                    "page": page,
                    "total_pages": total_pages,
                    "page_size": 2,
                },
                "results": [
                    {"id": f"{page}-a", "name": f"n{page}a"},
                    {"id": f"{page}-b", "name": f"n{page}b"},
                ],
            }
        )

    return handler


def test_iter_pages_walks_every_page(mock_client_factory):
    seen: list[int] = []
    client = mock_client_factory(_paged_handler(3, seen), api_key="nova_key_test")
    pages = list(iter_pages(client.templates.list, page_size=2))
    assert seen == [1, 2, 3]
    assert [p.pagination.page for p in pages] == [1, 2, 3]


def test_iter_items_flattens_all_pages(mock_client_factory):
    seen: list[int] = []
    client = mock_client_factory(_paged_handler(2, seen), api_key="nova_key_test")
    items = list(client.iter_items(client.templates.list))
    assert [i["id"] for i in items] == ["1-a", "1-b", "2-a", "2-b"]


def test_iter_pages_respects_starting_page(mock_client_factory):
    seen: list[int] = []
    client = mock_client_factory(_paged_handler(3, seen), api_key="nova_key_test")
    list(iter_items(client.templates.list, page=2))
    assert seen == [2, 3]


def test_iter_pages_stops_after_single_page(mock_client_factory):
    seen: list[int] = []
    client = mock_client_factory(_paged_handler(1, seen), api_key="nova_key_test")
    assert len(list(iter_pages(client.templates.list))) == 1
    assert seen == [1]


def test_iter_pages_rejects_invalid_start_page(mock_client_factory):
    client = mock_client_factory(_paged_handler(1, []), api_key="nova_key_test")
    with pytest.raises(NovaValidationError):
        list(iter_pages(client.templates.list, page=0))
