"""Helpers for walking paginated list endpoints."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any, TypeVar

from nova_sdk.exceptions import NovaValidationError
from nova_sdk.models import PaginatedResponse

T = TypeVar("T")

#: Upper bound on pages fetched by a single iteration, as a runaway guard.
MAX_PAGES = 10_000


def iter_pages(
    fetch: Callable[..., PaginatedResponse[T]],
    /,
    **kwargs: Any,
) -> Iterator[PaginatedResponse[T]]:
    """Yield successive pages from a ``list`` method.

    Example::

        for page in iter_pages(client.contacts.list, search="acme", page_size=100):
            print(page.pagination.page, len(page))

    Args:
        fetch: A bound ``list`` method such as ``client.contacts.list``.
        **kwargs: Arguments forwarded to ``fetch``. ``page`` selects the first page
            (default 1).
    """
    page_number = kwargs.pop("page", None)
    if page_number is None:
        page_number = 1
    if not isinstance(page_number, int) or page_number < 1:
        raise NovaValidationError("page must be a positive integer.")

    for _ in range(MAX_PAGES):
        result = fetch(page=page_number, **kwargs)
        yield result
        if not result.has_next or page_number >= result.pagination.total_pages:
            return
        page_number += 1


def iter_items(
    fetch: Callable[..., PaginatedResponse[T]],
    /,
    **kwargs: Any,
) -> Iterator[T]:
    """Yield every item across all pages of a ``list`` method.

    Example::

        for contact in iter_items(client.contacts.list, page_size=100):
            print(contact.email)
    """
    for page in iter_pages(fetch, **kwargs):
        yield from page.items
