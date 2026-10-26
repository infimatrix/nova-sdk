"""Base resource client class for Nova SDK."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nova_sdk.http import HTTPTransport


class BaseResource:
    """Base class providing access to the shared HTTP transport."""

    def __init__(self, transport: HTTPTransport) -> None:
        self._transport = transport
