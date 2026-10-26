"""Nova SDK Typed Exception Hierarchy.

All exceptions inherit from NovaError, providing structured, sanitized error context
including HTTP status code, backend error code, details dictionary, and correlation ID.
Sensitive secrets, authentication headers, and tokens are strictly prevented from leaking
into exception messages and string representations.
"""

from __future__ import annotations

from typing import Any


class NovaError(Exception):
    """Base exception class for all errors raised by the Nova SDK."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
        details: Any = None,
        correlation_id: str | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "SDK_ERROR"
        self.details = details if details is not None else {}
        self.correlation_id = correlation_id
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        parts = [self.message]
        metadata = []
        if self.status_code:
            metadata.append(f"status={self.status_code}")
        if self.error_code:
            metadata.append(f"code={self.error_code}")
        if self.correlation_id:
            metadata.append(f"correlation_id={self.correlation_id}")
        if metadata:
            parts.append(f"({', '.join(metadata)})")
        return " ".join(parts)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code!r}, "
            f"error_code={self.error_code!r}, "
            f"correlation_id={self.correlation_id!r})"
        )


class NovaConnectionError(NovaError):
    """Raised when an underlying network, DNS, or socket connection error occurs."""

    def __init__(
        self,
        message: str = "Failed to establish network connection to Nova API.",
        *,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(
            message,
            error_code="CONNECTION_ERROR",
            correlation_id=correlation_id,
        )


class NovaTimeoutError(NovaError):
    """Raised when an API request exceeds the configured network timeout limit."""

    def __init__(
        self,
        message: str = "Request to Nova API timed out.",
        *,
        correlation_id: str | None = None,
    ) -> None:
        super().__init__(
            message,
            error_code="REQUEST_TIMEOUT",
            correlation_id=correlation_id,
        )


class NovaAPIError(NovaError):
    """Base exception for HTTP 4xx and 5xx responses returned by the Nova API."""

    pass


class NovaRedirectError(NovaAPIError):
    """Raised when the API returns an unexpected HTTP 3xx redirect response."""

    def __init__(
        self,
        message: str = "Unexpected redirect received from Nova API.",
        *,
        status_code: int = 301,
        error_code: str | None = "UNEXPECTED_REDIRECT",
        details: Any = None,
        correlation_id: str | None = None,
        location: str | None = None,
    ) -> None:
        self.location = location
        super().__init__(
            message,
            status_code=status_code,
            error_code=error_code,
            details=details,
            correlation_id=correlation_id,
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code!r}, "
            f"error_code={self.error_code!r}, "
            f"location={self.location!r}, "
            f"correlation_id={self.correlation_id!r})"
        )


class NovaAuthenticationError(NovaAPIError):
    """Raised when authentication fails (HTTP 401 Unauthorized).

    Indicates an invalid, expired, or missing API key or JWT access token.
    """

    pass


class NovaPermissionError(NovaAPIError):
    """Raised when the user lacks required permissions or tenant access (HTTP 403 Forbidden)."""

    pass


class NovaNotFoundError(NovaAPIError):
    """Raised when the requested resource or tenant was not found (HTTP 404 Not Found)."""

    pass


class NovaValidationError(NovaAPIError):
    """Raised when request payload or parameter validation fails (HTTP 400 Bad Request)."""

    pass


class NovaRateLimitError(NovaAPIError):
    """Raised when request rate limits have been exceeded (HTTP 429 Too Many Requests)."""

    def __init__(
        self,
        message: str = "Rate limit exceeded.",
        *,
        status_code: int = 429,
        error_code: str | None = "RATE_LIMIT_EXCEEDED",
        details: Any = None,
        correlation_id: str | None = None,
        retry_after: float | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(
            message,
            status_code=status_code,
            error_code=error_code,
            details=details,
            correlation_id=correlation_id,
        )

    def _format_message(self) -> str:
        parts = [self.message]
        metadata = []
        if self.status_code:
            metadata.append(f"status={self.status_code}")
        if self.error_code:
            metadata.append(f"code={self.error_code}")
        if self.retry_after is not None:
            metadata.append(f"retry_after={self.retry_after}s")
        if self.correlation_id:
            metadata.append(f"correlation_id={self.correlation_id}")
        if metadata:
            parts.append(f"({', '.join(metadata)})")
        return " ".join(parts)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code!r}, "
            f"error_code={self.error_code!r}, "
            f"retry_after={self.retry_after!r}, "
            f"correlation_id={self.correlation_id!r})"
        )


class NovaServerError(NovaAPIError):
    """Raised when the Nova server encounters an internal error (HTTP 5xx)."""

    pass


def map_api_error(
    status_code: int,
    *,
    message: str | None = None,
    error_code: str | None = None,
    details: Any = None,
    correlation_id: str | None = None,
    retry_after: float | None = None,
    location: str | None = None,
) -> NovaAPIError:
    """Map an HTTP status code and parsed error envelope into a typed Nova exception."""
    default_msg = message or f"API request failed with status {status_code}."
    code = error_code or "API_ERROR"

    if 300 <= status_code < 400:
        return NovaRedirectError(
            default_msg,
            status_code=status_code,
            error_code=error_code or "UNEXPECTED_REDIRECT",
            details=details,
            correlation_id=correlation_id,
            location=location,
        )
    elif status_code == 401:
        return NovaAuthenticationError(
            default_msg,
            status_code=status_code,
            error_code=code or "AUTHENTICATION_FAILED",
            details=details,
            correlation_id=correlation_id,
        )
    elif status_code == 403:
        return NovaPermissionError(
            default_msg,
            status_code=status_code,
            error_code=code or "PERMISSION_DENIED",
            details=details,
            correlation_id=correlation_id,
        )
    elif status_code == 404:
        return NovaNotFoundError(
            default_msg,
            status_code=status_code,
            error_code=code or "NOT_FOUND",
            details=details,
            correlation_id=correlation_id,
        )
    elif status_code == 400:
        return NovaValidationError(
            default_msg,
            status_code=status_code,
            error_code=code or "VALIDATION_ERROR",
            details=details,
            correlation_id=correlation_id,
        )
    elif status_code == 429:
        return NovaRateLimitError(
            default_msg,
            status_code=status_code,
            error_code=code or "RATE_LIMIT_EXCEEDED",
            details=details,
            correlation_id=correlation_id,
            retry_after=retry_after,
        )
    elif status_code >= 500:
        return NovaServerError(
            default_msg,
            status_code=status_code,
            error_code=code or "SERVER_ERROR",
            details=details,
            correlation_id=correlation_id,
        )
    else:
        return NovaAPIError(
            default_msg,
            status_code=status_code,
            error_code=code,
            details=details,
            correlation_id=correlation_id,
        )
