"""Tests for Nova SDK typed exception hierarchy and response mapping."""

from __future__ import annotations

from nova_sdk.exceptions import (
    NovaAPIError,
    NovaAuthenticationError,
    NovaError,
    NovaNotFoundError,
    NovaPermissionError,
    NovaRateLimitError,
    NovaRedirectError,
    NovaServerError,
    NovaValidationError,
    map_api_error,
)


def test_exception_inheritance():
    err = NovaAuthenticationError("Invalid credentials", status_code=401)
    assert isinstance(err, NovaAPIError)
    assert isinstance(err, NovaError)
    assert isinstance(err, Exception)


def test_exception_formatting():
    err = NovaError(
        "Invalid request payload.",
        status_code=400,
        error_code="VALIDATION_ERROR",
        correlation_id="req-999",
    )
    msg = str(err)
    assert "Invalid request payload." in msg
    assert "status=400" in msg
    assert "code=VALIDATION_ERROR" in msg
    assert "correlation_id=req-999" in msg


def test_map_api_error_codes():
    # 400 -> ValidationError
    err400 = map_api_error(400, message="Bad email format")
    assert isinstance(err400, NovaValidationError)
    assert err400.status_code == 400

    # 401 -> AuthenticationError
    err401 = map_api_error(401, message="Token expired")
    assert isinstance(err401, NovaAuthenticationError)
    assert err401.status_code == 401

    # 403 -> PermissionError
    err403 = map_api_error(403, message="Access denied to workspace")
    assert isinstance(err403, NovaPermissionError)
    assert err403.status_code == 403

    # 404 -> NotFoundError
    err404 = map_api_error(404, message="Template not found")
    assert isinstance(err404, NovaNotFoundError)
    assert err404.status_code == 404

    # 429 -> RateLimitError with retry_after
    err429 = map_api_error(429, message="Throttled", retry_after=12.5)
    assert isinstance(err429, NovaRateLimitError)
    assert err429.status_code == 429
    assert err429.retry_after == 12.5
    assert "retry_after=12.5s" in str(err429)
    assert "retry_after=12.5" in repr(err429)

    # 301 / 302 / 307 -> RedirectError
    err301 = map_api_error(
        301, message="Moved permanently", location="/api/v1/contacts/"
    )
    assert isinstance(err301, NovaRedirectError)
    assert err301.status_code == 301
    assert err301.location == "/api/v1/contacts/"
    assert "location='/api/v1/contacts/'" in repr(err301)

    err302 = map_api_error(302, message="Found")
    assert isinstance(err302, NovaRedirectError)
    assert err302.status_code == 302

    err307 = map_api_error(307, message="Temporary redirect")
    assert isinstance(err307, NovaRedirectError)
    assert err307.status_code == 307

    # 500 / 502 / 503 -> ServerError
    err500 = map_api_error(500, message="Internal error")
    assert isinstance(err500, NovaServerError)
    assert err500.status_code == 500

    err503 = map_api_error(503, message="Service unavailable")
    assert isinstance(err503, NovaServerError)
    assert err503.status_code == 503

    # Unmapped status -> Generic NovaAPIError
    err418 = map_api_error(418, message="Teapot")
    assert isinstance(err418, NovaAPIError)
    assert err418.status_code == 418


def test_rate_limit_error_repr_includes_retry_after():
    err_with_retry = NovaRateLimitError(
        "Rate limit exceeded.",
        retry_after=45.0,
        correlation_id="req-rate-limit",
    )
    repr_str = repr(err_with_retry)
    assert "retry_after=45.0" in repr_str
    assert "correlation_id='req-rate-limit'" in repr_str
    assert "retry_after=45.0s" in str(err_with_retry)

    err_without_retry = NovaRateLimitError("Rate limit exceeded.")
    assert "retry_after=None" in repr(err_without_retry)


def test_redirect_error_inheritance_and_attributes():
    err = NovaRedirectError(
        "Unexpected redirect.",
        status_code=308,
        location="https://api.novamail.io/api/v1/health/",
        correlation_id="corr-red-1",
    )
    assert isinstance(err, NovaAPIError)
    assert isinstance(err, NovaError)
    assert err.status_code == 308
    assert err.location == "https://api.novamail.io/api/v1/health/"
    assert "location='https://api.novamail.io/api/v1/health/'" in repr(err)
