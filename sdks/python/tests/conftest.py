"""Test fixtures and mock helpers for Nova SDK test suite."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest

# Ensure sdks/python/tests is on sys.path for local helper imports
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from helpers import create_mock_transport  # noqa: E402

from nova_sdk import NovaClient  # noqa: E402


@pytest.fixture
def sample_tenant_id() -> str:
    return "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def sample_api_key() -> str:
    return "nova_key_test_secret_1234567890abcdef"


@pytest.fixture
def mock_client_factory():
    """Factory fixture for instantiating a NovaClient wired to a mock handler."""

    def _factory(
        handler: Callable[[httpx.Request], httpx.Response], **kwargs: Any
    ) -> NovaClient:
        transport = create_mock_transport(handler)
        mock_http = httpx.Client(transport=transport)
        return NovaClient(_http_client=mock_http, **kwargs)

    return _factory


@pytest.fixture
def async_client_factory():
    """Factory fixture for an AsyncNovaClient wired to a mock handler."""
    from nova_sdk.aio import AsyncNovaClient

    def _factory(
        handler: Callable[[httpx.Request], httpx.Response], **kwargs: Any
    ) -> AsyncNovaClient:
        mock_http = httpx.AsyncClient(transport=create_mock_transport(handler))
        return AsyncNovaClient(_http_client=mock_http, **kwargs)

    return _factory
