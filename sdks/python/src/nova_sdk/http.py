"""HTTP Transport and safe request execution engine for Nova SDK."""

from __future__ import annotations

import logging
import posixpath
import random
import re
import time
from collections.abc import Mapping
from typing import Any
from urllib.parse import unquote, urlsplit, urlunsplit

import httpx

from nova_sdk.config import NovaConfig
from nova_sdk.exceptions import (
    NovaAPIError,
    NovaConnectionError,
    NovaError,
    NovaRedirectError,
    NovaTimeoutError,
    NovaValidationError,
    map_api_error,
)
from nova_sdk.models import ApiResponse, EnvelopeMeta

logger = logging.getLogger("nova_sdk.http")

# HTTP methods that are inherently idempotent and safe to retry on transient failure
IDEMPOTENT_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

# Known static/media/data file extensions that should NOT have a trailing slash appended
KNOWN_FILE_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".csv",
        ".gif",
        ".gz",
        ".htm",
        ".html",
        ".jpeg",
        ".jpg",
        ".json",
        ".pdf",
        ".png",
        ".svg",
        ".tar",
        ".txt",
        ".webp",
        ".xml",
        ".yaml",
        ".yml",
        ".zip",
    }
)


def _sanitize_redirect_location(location: str | None) -> str | None:
    """Sanitize redirect location URL by removing any embedded user credentials."""
    if not location or not location.strip():
        return None
    cleaned = location.strip()
    try:
        parts = urlsplit(cleaned)
        if "@" in parts.netloc:
            safe_netloc = parts.netloc.split("@", 1)[-1]
            parts = parts._replace(netloc=safe_netloc)
            return urlunsplit(parts)
        return cleaned
    except Exception:
        return "<invalid-redirect-url>"


def _sanitize_error_text(text: str | None, status_code: int) -> str:
    """Extract a concise, safe summary from a non-JSON or HTML error response."""
    if not text or not text.strip():
        return f"HTTP {status_code} Error"

    raw = text.strip()
    lower_raw = raw.lower()

    # Detect HTML responses
    if (
        "<html" in lower_raw
        or "<!doctype html" in lower_raw
        or "<head" in lower_raw
        or "<body" in lower_raw
    ):
        title_match = re.search(r"<title>(.*?)</title>", raw, re.IGNORECASE | re.DOTALL)
        if title_match:
            title_text = re.sub(r"\s+", " ", title_match.group(1)).strip()
            if title_text and len(title_text) <= 120:
                return f"HTTP {status_code} Error: {title_text}"
        return f"HTTP {status_code} Error (HTML response received)"

    collapsed = re.sub(r"\s+", " ", raw)
    if len(collapsed) > 200:
        return f"{collapsed[:197]}..."
    return collapsed


class TransportCore:
    """Request/response logic shared by the sync and async transports."""

    config: NovaConfig

    def build_url(self, endpoint: str) -> str:
        """Construct a fully qualified API endpoint URL under /api/v1/ prefix."""
        endpoint_str = endpoint.strip() if endpoint else ""
        parsed = urlsplit(endpoint_str)
        path = parsed.path.strip().lstrip("/")

        # Preserve and avoid duplicating /api/v1/ prefix
        if path == "api/v1":
            path = ""
        elif path.startswith("api/v1/"):
            path = path[len("api/v1/") :].lstrip("/")

        # An id of "." or ".." would be normalised away by HTTP clients and intermediaries,
        # silently addressing a different endpoint (e.g. templates/../ -> /api/v1/).
        for segment in path.split("/"):
            if unquote(segment) in (".", ".."):
                raise NovaValidationError(
                    "Path identifiers must not be '.' or '..'.",
                )

        # Decide whether to append trailing slash to path
        if path:
            if not path.endswith("/"):
                # Check if the final path segment has a known file extension
                last_segment = path.split("/")[-1]
                _, ext = posixpath.splitext(last_segment)
                if ext.lower() not in KNOWN_FILE_EXTENSIONS:
                    path = f"{path}/"
            full_path = f"/api/v1/{path}"
        else:
            full_path = "/api/v1/"

        base = self.config.base_url.rstrip("/")
        url = f"{base}{full_path}"

        if parsed.query:
            url = f"{url}?{parsed.query}"
        if parsed.fragment:
            url = f"{url}#{parsed.fragment}"

        return url

    def _prepare_headers(
        self,
        custom_headers: Mapping[str, str] | None = None,
        tenant_id: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, str]:
        """Assemble request headers incorporating authentication and tenant context."""
        headers = self.config.get_headers()

        # Allow per-request tenant override
        if tenant_id:
            import uuid

            try:
                validated_uuid = str(uuid.UUID(str(tenant_id).strip()))
                headers["X-Tenant-ID"] = validated_uuid
            except ValueError as exc:
                raise NovaValidationError(
                    f"tenant_id must be a valid UUID string, got {tenant_id!r}."
                ) from exc

        # Correlation ID
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id.strip()

        if custom_headers:
            headers.update(custom_headers)

        return headers

    def _parse_retry_after(self, response: httpx.Response) -> float | None:
        """Parse Retry-After header as seconds if present."""
        retry_header = response.headers.get("Retry-After")
        if not retry_header:
            return None
        try:
            return max(0.0, float(retry_header))
        except (ValueError, TypeError):
            return None

    def _compute_backoff_delay(
        self, attempt: int, retry_after: float | None = None
    ) -> float:
        """Compute bounded exponential backoff delay with jitter."""
        if retry_after is not None:
            # Bound retry-after to at most 30 seconds to prevent indefinite stalls
            return min(30.0, retry_after)

        delay = self.config.retry_backoff_factor * (2**attempt)
        if self.config.retry_jitter:
            delay = delay * (0.5 + random.random() * 0.5)

        return min(30.0, max(0.05, delay))

    def _parse_success_response(self, response: httpx.Response) -> ApiResponse[Any]:
        """Parse successful 2xx responses and unwrap Nova envelope payloads."""
        correlation_id = response.headers.get("X-Correlation-ID")

        # HTTP 204 No Content
        if response.status_code == 204 or not response.content:
            return ApiResponse(
                data=None,
                success=True,
                message="Operation completed successfully.",
                meta=EnvelopeMeta(correlation_id=correlation_id),
            )

        # Check content type for CSV or binary responses
        content_type = response.headers.get("Content-Type", "")
        if "text/csv" in content_type:
            return ApiResponse(
                data=response.text,
                success=True,
                message="CSV export generated.",
                meta=EnvelopeMeta(correlation_id=correlation_id),
            )

        try:
            payload = response.json()
        except Exception:
            if "json" in content_type.lower():
                # The server declared JSON but sent something else: never report that as success.
                raise NovaAPIError(
                    f"Invalid JSON in HTTP {response.status_code} response.",
                    status_code=response.status_code,
                    error_code="INVALID_RESPONSE",
                    correlation_id=correlation_id,
                ) from None
            # Non-JSON or binary response
            return ApiResponse(
                data=response.text,
                success=True,
                message="Raw response received.",
                meta=EnvelopeMeta(correlation_id=correlation_id),
            )

        if isinstance(payload, dict):
            # Standard envelope response: { success, message, data, meta }
            if "success" in payload and "data" in payload:
                meta_dict = payload.get("meta") or {}
                if not meta_dict.get("correlation_id") and correlation_id:
                    meta_dict["correlation_id"] = correlation_id

                meta = EnvelopeMeta.from_dict(meta_dict)
                return ApiResponse(
                    data=payload.get("data"),
                    success=bool(payload.get("success", True)),
                    message=str(
                        payload.get("message", "Operation completed successfully.")
                    ),
                    meta=meta,
                )

        # Unenveloped JSON response fallback
        return ApiResponse(
            data=payload,
            success=True,
            message="Operation completed successfully.",
            meta=EnvelopeMeta(correlation_id=correlation_id),
        )

    def _handle_redirect_response(self, response: httpx.Response) -> None:
        """Handle unexpected HTTP 3xx redirect response safely."""
        correlation_id = response.headers.get("X-Correlation-ID")
        raw_location = response.headers.get("Location")
        clean_location = _sanitize_redirect_location(raw_location)
        dest = f" to {clean_location}" if clean_location else ""
        message = f"Unexpected HTTP {response.status_code} redirect{dest}."
        details = {"location": clean_location} if clean_location else {}
        raise NovaRedirectError(
            message=message,
            status_code=response.status_code,
            details=details,
            correlation_id=correlation_id,
            location=clean_location,
        )

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Parse structured error envelope and raise corresponding typed NovaAPIError."""
        correlation_id = response.headers.get("X-Correlation-ID")
        retry_after = self._parse_retry_after(response)

        message: str | None = None
        error_code: str | None = None
        details: Any = None

        try:
            payload = response.json()
            if isinstance(payload, dict):
                # Check for envelope meta
                meta_dict = payload.get("meta") or {}
                correlation_id = meta_dict.get("correlation_id") or correlation_id

                # Check error object: { error: { code, message, details } }
                err_obj = payload.get("error") or payload.get("errors")
                if isinstance(err_obj, dict):
                    error_code = err_obj.get("code")
                    message = err_obj.get("message")
                    details = err_obj.get("details")
                elif isinstance(err_obj, str):
                    # Legacy non-enveloped bodies such as {"error": "Tenant context required."}
                    message = err_obj

                # Check top-level message if not in error object
                if not message:
                    message = payload.get("message") or payload.get("detail")

                # If details were not in error object, check if entire payload is a DRF error dict
                if details is None:
                    details = {
                        k: v
                        for k, v in payload.items()
                        if k
                        not in ("success", "message", "error", "errors", "meta", "data")
                    }
            elif isinstance(payload, list):
                details = {"errors": payload}
                message = "Validation failed for request data."
        except Exception:
            message = _sanitize_error_text(response.text, response.status_code)

        if not message:
            message = _sanitize_error_text(response.text, response.status_code)

        raise map_api_error(
            response.status_code,
            message=message,
            error_code=error_code,
            details=details,
            correlation_id=correlation_id,
            retry_after=retry_after,
        )


class HTTPTransport(TransportCore):
    """Manages low-level HTTP communication with the Nova REST API."""

    def __init__(
        self,
        config: NovaConfig,
        *,
        client: httpx.Client | None = None,
    ) -> None:
        self.config = config
        self._custom_client = client is not None
        self._client = client or httpx.Client(
            timeout=httpx.Timeout(config.timeout),
            verify=config.verify_ssl,
            follow_redirects=False,  # Prevent credential leakage across redirect hops
        )

    @property
    def is_closed(self) -> bool:
        return self._client.is_closed

    def close(self) -> None:
        """Close the underlying HTTP client session."""
        if not self._custom_client and not self._client.is_closed:
            self._client.close()

    def __enter__(self) -> HTTPTransport:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def _send_request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        headers: Mapping[str, str] | None = None,
        tenant_id: str | None = None,
        correlation_id: str | None = None,
        allow_retry: bool | None = None,
    ) -> httpx.Response:
        """Execute an HTTP request against the Nova API with safe retry and error semantics."""
        http_method = method.strip().upper()
        url = self.build_url(endpoint)
        req_headers = self._prepare_headers(
            custom_headers=headers,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
        )

        # Retries are permitted ONLY for idempotent methods unless explicitly overridden
        # Side-effect operations (POST, PUT, PATCH, DELETE) are never automatically retried by default.
        is_safe_to_retry = (
            allow_retry
            if allow_retry is not None
            else (http_method in IDEMPOTENT_METHODS)
        )
        max_attempts = (self.config.max_retries + 1) if is_safe_to_retry else 1

        last_exception: Exception | None = None

        for attempt in range(max_attempts):
            try:
                response = self._client.request(
                    method=http_method,
                    url=url,
                    params=params,
                    json=json,
                    data=data,
                    files=files,
                    headers=req_headers,
                )

                # 1. Successful 2xx responses ONLY
                if 200 <= response.status_code < 300:
                    return response

                # 2. Unexpected 3xx redirects (must NOT be treated as success or retried)
                if 300 <= response.status_code < 400:
                    self._handle_redirect_response(response)

                # Check if status code is eligible for retry on an idempotent request
                retryable = (
                    is_safe_to_retry
                    and attempt < max_attempts - 1
                    and response.status_code in self.config.retryable_status_codes
                )

                if retryable:
                    retry_after = self._parse_retry_after(response)
                    delay = self._compute_backoff_delay(attempt, retry_after)
                    logger.warning(
                        "Nova API request %s %s returned %d. Retrying in %.2fs (attempt %d/%d)...",
                        http_method,
                        endpoint,
                        response.status_code,
                        delay,
                        attempt + 1,
                        self.config.max_retries,
                    )
                    time.sleep(delay)
                    continue

                # Non-retryable error or retries exhausted -> raise typed exception
                self._handle_error_response(response)

            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                last_exception = exc
                if is_safe_to_retry and attempt < max_attempts - 1:
                    delay = self._compute_backoff_delay(attempt)
                    logger.warning(
                        "Connection error on %s %s: %s. Retrying in %.2fs (attempt %d/%d)...",
                        http_method,
                        endpoint,
                        exc,
                        delay,
                        attempt + 1,
                        self.config.max_retries,
                    )
                    time.sleep(delay)
                    continue
                corr_id = req_headers.get("X-Correlation-ID")
                raise NovaConnectionError(
                    f"Failed to connect to Nova API at {url}: {exc}",
                    correlation_id=corr_id,
                ) from exc

            except httpx.TimeoutException as exc:
                last_exception = exc
                if is_safe_to_retry and attempt < max_attempts - 1:
                    delay = self._compute_backoff_delay(attempt)
                    logger.warning(
                        "Timeout on %s %s. Retrying in %.2fs (attempt %d/%d)...",
                        http_method,
                        endpoint,
                        delay,
                        attempt + 1,
                        self.config.max_retries,
                    )
                    time.sleep(delay)
                    continue
                corr_id = req_headers.get("X-Correlation-ID")
                raise NovaTimeoutError(
                    f"Request to Nova API timed out after {self.config.timeout}s: {exc}",
                    correlation_id=corr_id,
                ) from exc

            except NovaError:
                # Re-raise explicit Nova errors
                raise

            except Exception as exc:
                corr_id = req_headers.get("X-Correlation-ID")
                raise NovaError(
                    f"Unexpected error during API request to {url}: {exc}",
                    correlation_id=corr_id,
                ) from exc

        # Fallback if loop ended unexpectedly
        if last_exception:
            raise NovaConnectionError(
                f"Request to {url} failed after retries: {last_exception}",
                correlation_id=req_headers.get("X-Correlation-ID"),
            ) from last_exception
        raise NovaError("Request terminated without a response.")

    def request_raw(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        headers: Mapping[str, str] | None = None,
        tenant_id: str | None = None,
        correlation_id: str | None = None,
        allow_retry: bool | None = None,
    ) -> httpx.Response:
        """Execute an HTTP request against the Nova API and return the raw httpx.Response.

        Used for non-JSON endpoints such as CSV exports or file downloads.
        All authentication, tenant context, redirect protections, retry bounds,
        and error mappings are strictly enforced.
        """
        return self._send_request(
            method=method,
            endpoint=endpoint,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=headers,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            allow_retry=allow_retry,
        )

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
        headers: Mapping[str, str] | None = None,
        tenant_id: str | None = None,
        correlation_id: str | None = None,
        allow_retry: bool | None = None,
    ) -> ApiResponse[Any]:
        """Execute an HTTP request against the Nova API with safe retry semantics."""
        raw_response = self._send_request(
            method=method,
            endpoint=endpoint,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=headers,
            tenant_id=tenant_id,
            correlation_id=correlation_id,
            allow_retry=allow_retry,
        )
        return self._parse_success_response(raw_response)
