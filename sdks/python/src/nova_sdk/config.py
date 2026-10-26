"""Nova SDK Configuration and Validation Module.

Provides robust validation for client settings including base URL normalization,
timeout boundaries, bounded exponential backoff parameters, and secret redacting repr.
"""

from __future__ import annotations

import os
import re
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from urllib.parse import urlparse

from nova_sdk._version import __version__
from nova_sdk.exceptions import NovaValidationError


def _clean_credential(val: str | None) -> str | None:
    """Normalize a credential by stripping surrounding whitespace and leading 'Bearer ' prefixes."""
    if val is None:
        return None
    cleaned = str(val).strip()
    while cleaned.lower().startswith("bearer ") or cleaned.lower() == "bearer":
        if cleaned.lower() == "bearer":
            return None
        cleaned = cleaned[7:].strip()
    return cleaned if cleaned else None


def _sanitize_secret(val: str | None) -> str:
    """Return a masked representation of a sensitive credential."""
    cleaned = _clean_credential(val)
    if not cleaned:
        return "<None>"
    if len(cleaned) <= 12:
        return "[REDACTED]"
    return f"{cleaned[:8]}...[REDACTED]"


@dataclass
class NovaConfig:
    """Configuration container for NovaClient HTTP transport and behavior."""

    base_url: str = field(
        default_factory=lambda: os.getenv("NOVA_BASE_URL", "http://localhost:8000")
    )
    api_key: str | None = field(default_factory=lambda: os.getenv("NOVA_API_KEY", None))
    access_token: str | None = field(
        default_factory=lambda: os.getenv("NOVA_ACCESS_TOKEN", None)
    )
    tenant_id: str | None = field(
        default_factory=lambda: os.getenv("NOVA_TENANT_ID", None)
    )
    timeout: float = 30.0
    max_retries: int = 3
    retry_backoff_factor: float = 0.5
    retry_jitter: bool = True
    retryable_status_codes: tuple[int, ...] = (429, 502, 503, 504)
    verify_ssl: bool = True
    default_headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate all configuration attributes strictly."""
        # 1. Base URL validation & normalization
        if not self.base_url or not isinstance(self.base_url, str):
            raise NovaValidationError("base_url must be a non-empty string.")

        parsed = urlparse(self.base_url.strip())
        if parsed.scheme.lower() not in ("http", "https"):
            raise NovaValidationError(
                f"Invalid base_url scheme {parsed.scheme!r}. Must be 'http' or 'https'."
            )
        if not parsed.netloc:
            raise NovaValidationError(
                f"Invalid base_url {self.base_url!r}. Must include host/domain."
            )

        # Normalize: strip trailing slash and path /api/v1 if inadvertently provided by user
        clean_url = self.base_url.strip().rstrip("/")
        # Remove trailing /api/v1 if user passed base_url="http://localhost:8000/api/v1"
        clean_url = re.sub(r"/api(/v1)?$", "", clean_url)
        self.base_url = clean_url

        # 2. Timeout validation
        if not isinstance(self.timeout, (int, float)) or self.timeout <= 0:
            raise NovaValidationError(
                f"timeout must be a positive number, got {self.timeout!r}."
            )

        # 3. Retry limits validation
        if not isinstance(self.max_retries, int) or self.max_retries < 0:
            raise NovaValidationError(
                f"max_retries must be a non-negative integer, got {self.max_retries!r}."
            )
        if self.max_retries > 10:
            raise NovaValidationError(
                f"max_retries cannot exceed 10 for safety, got {self.max_retries}."
            )

        if (
            not isinstance(self.retry_backoff_factor, (int, float))
            or self.retry_backoff_factor < 0
        ):
            raise NovaValidationError(
                "retry_backoff_factor must be a non-negative number."
            )

        # 4. Tenant ID validation (if specified)
        if self.tenant_id:
            try:
                uuid_obj = uuid.UUID(str(self.tenant_id).strip())
                self.tenant_id = str(uuid_obj)
            except (ValueError, AttributeError) as exc:
                raise NovaValidationError(
                    f"tenant_id must be a valid UUID string, got {self.tenant_id!r}."
                ) from exc

        # 5. Header validation
        if not isinstance(self.default_headers, Mapping):
            raise NovaValidationError("default_headers must be a dictionary.")

        # 6. Normalize credentials (strip leading 'Bearer ' and whitespace)
        self.api_key = _clean_credential(self.api_key)
        self.access_token = _clean_credential(self.access_token)

    def get_headers(self) -> dict[str, str]:
        """Compute the default HTTP headers according to current authentication & tenant context."""
        headers = dict(self.default_headers)
        headers.setdefault("Accept", "application/json")
        headers.setdefault("User-Agent", f"Nova-Python-SDK/{__version__}")

        # Prioritize API Key if provided, then JWT Access Token
        clean_key = _clean_credential(self.api_key)
        clean_token = _clean_credential(self.access_token)
        if clean_key:
            headers["Authorization"] = f"Bearer {clean_key}"
        elif clean_token:
            headers["Authorization"] = f"Bearer {clean_token}"

        # Tenant header
        if self.tenant_id:
            headers["X-Tenant-ID"] = self.tenant_id

        return headers

    def __repr__(self) -> str:
        return (
            f"NovaConfig("
            f"base_url={self.base_url!r}, "
            f"api_key={_sanitize_secret(self.api_key)}, "
            f"access_token={_sanitize_secret(self.access_token)}, "
            f"tenant_id={self.tenant_id!r}, "
            f"timeout={self.timeout}, "
            f"max_retries={self.max_retries}, "
            f"verify_ssl={self.verify_ssl})"
        )
