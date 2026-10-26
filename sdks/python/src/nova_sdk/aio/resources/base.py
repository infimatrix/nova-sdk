"""Base class of the asynchronous resource clients."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nova_sdk.aio.http import AsyncHTTPTransport


class BaseResource:
    """Base class providing access to the shared asynchronous HTTP transport."""

    def __init__(self, transport: AsyncHTTPTransport) -> None:
        self._transport = transport
