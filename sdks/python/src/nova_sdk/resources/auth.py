"""Authentication and API Key resource client for Nova SDK."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from nova_sdk._model_base import parse_model
from nova_sdk.exceptions import NovaValidationError
from nova_sdk.models import PaginatedResponse
from nova_sdk.resources.base import BaseResource
from nova_sdk.schemas import (
    APIKey,
    APIKeyCreate,
    ChangePasswordResponse,
    ForgotPasswordResponse,
    Login,
    Logout,
    ResetPasswordResponse,
    TokenRefresh,
    UserMe,
    UserRegister,
    ValidateResetTokenResponse,
)

if TYPE_CHECKING:
    from nova_sdk.client import NovaClient
    from nova_sdk.http import HTTPTransport


class APIKeysResource(BaseResource):
    """Resource client for listing, creating, and revoking API keys."""

    def list(
        self,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> PaginatedResponse[APIKey]:
        """List active API keys for the authenticated user.

        Endpoint: GET /api/v1/auth/api-keys/
        """
        response = self._transport.request("GET", "auth/api-keys/", params=params)
        return PaginatedResponse.from_response(response, item_parser=APIKey.from_dict)

    def create(
        self,
        *,
        name: str = "Default API Key",
        expires_at: str | None = None,
    ) -> APIKeyCreate:
        """Generate a new API key for the authenticated user.

        Endpoint: POST /api/v1/auth/api-keys/
        Returns the raw secret key string ONCE upon creation.
        """
        if not name or not str(name).strip():
            raise NovaValidationError("name must be a non-empty string.")

        payload: dict[str, Any] = {"name": str(name).strip()}
        if expires_at is not None:
            payload["expires_at"] = expires_at

        response = self._transport.request("POST", "auth/api-keys/", json=payload)
        return parse_model(APIKeyCreate, response.data or {})

    def revoke(self, api_key_id: str) -> None:
        """Revoke / soft-delete an existing API key for the authenticated user.

        Endpoint: DELETE /api/v1/auth/api-keys/{id}/
        """
        if not api_key_id or not str(api_key_id).strip():
            raise NovaValidationError("api_key_id must be a non-empty string.")
        clean_id = quote(str(api_key_id).strip(), safe="")
        self._transport.request("DELETE", f"auth/api-keys/{clean_id}/")

    # Alias delete to revoke
    delete = revoke


class AuthResource(BaseResource):
    """Resource client for Authentication, Tokens, Current Profile, and API Keys."""

    def __init__(
        self,
        transport: HTTPTransport,
        client: NovaClient | None = None,
    ) -> None:
        super().__init__(transport)
        self._client = client
        self.api_keys = APIKeysResource(transport)

    def login(
        self,
        *,
        email: str,
        password: str,
        set_current_token: bool = False,
    ) -> Login:
        """Authenticate user with email and password.

        Endpoint: POST /api/v1/auth/login/
        Returns JWT access token, refresh token, user profile, and tenant memberships.

        Args:
            email: Registered account email address.
            password: User password.
            set_current_token: If True, sets the returned access token on the client.
        """
        if not email or not isinstance(email, str) or not email.strip():
            raise NovaValidationError("email must be a non-empty string.")
        if not password or not isinstance(password, str) or not password:
            raise NovaValidationError("password must be a non-empty string.")

        payload = {"email": email.strip(), "password": password}
        response = self._transport.request("POST", "auth/login/", json=payload)
        data: dict[str, Any] = response.data or {}

        if set_current_token and self._client and "access" in data:
            self._client.set_auth_token(data["access"])

        return Login.from_dict(data)

    def register(
        self,
        *,
        email: str,
        password: str,
        first_name: str | None = None,
        last_name: str | None = None,
        username: str | None = None,
        organization_name: str | None = None,
        set_current_token: bool = False,
    ) -> UserRegister:
        """Register a new user account (optionally creating an organization).

        Endpoint: POST /api/v1/auth/register/
        Returns JWT access/refresh tokens, the user profile, and tenant memberships.

        Args:
            email: Account email address (must be unique).
            password: Account password (minimum 8 characters, validated server-side).
            first_name: Optional given name.
            last_name: Optional family name.
            username: Optional username.
            organization_name: Optional name of an organization to create for the user.
            set_current_token: If True, sets the returned access token on the client.

        Raises:
            NovaValidationError: If email or password is missing, or the server
                rejects the payload (e.g. duplicate email, weak password).
        """
        if not email or not isinstance(email, str) or not email.strip():
            raise NovaValidationError("email must be a non-empty string.")
        if not password or not isinstance(password, str):
            raise NovaValidationError("password must be a non-empty string.")

        payload: dict[str, Any] = {"email": email.strip(), "password": password}
        optional = {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "organization_name": organization_name,
        }
        payload.update({k: v for k, v in optional.items() if v is not None})

        response = self._transport.request("POST", "auth/register/", json=payload)
        data: dict[str, Any] = response.data or {}

        if set_current_token and self._client and "access" in data:
            self._client.set_auth_token(data["access"])

        return UserRegister.from_dict(data)

    def forgot_password(self, email: str) -> ForgotPasswordResponse:
        """Request a password-reset email.

        Endpoint: POST /api/v1/auth/forgot-password/
        The server always responds with a generic success message, whether or not
        the address belongs to an account.
        """
        if not email or not isinstance(email, str) or not email.strip():
            raise NovaValidationError("email must be a non-empty string.")
        response = self._transport.request(
            "POST", "auth/forgot-password/", json={"email": email.strip()}
        )
        return parse_model(ForgotPasswordResponse, response.data or {})

    def validate_reset_token(
        self, *, uid: str, token: str
    ) -> ValidateResetTokenResponse:
        """Check whether a password-reset link (uid + token) is still valid.

        Endpoint: POST /api/v1/auth/reset-password/validate/
        """
        payload = self._reset_identity(uid, token)
        response = self._transport.request(
            "POST", "auth/reset-password/validate/", json=payload
        )
        return parse_model(ValidateResetTokenResponse, response.data or {})

    def reset_password(
        self,
        *,
        uid: str,
        token: str,
        new_password: str,
        confirm_password: str | None = None,
    ) -> ResetPasswordResponse:
        """Complete a password reset using the uid and token from the reset email.

        Endpoint: POST /api/v1/auth/reset-password/

        Args:
            uid: Encoded user identifier from the reset link.
            token: Single-use reset token from the reset link.
            new_password: The new password (validated server-side).
            confirm_password: Optional confirmation; must equal new_password if given.
        """
        payload = self._reset_identity(uid, token)
        if not new_password or not isinstance(new_password, str):
            raise NovaValidationError("new_password must be a non-empty string.")
        payload["new_password"] = new_password
        if confirm_password is not None:
            payload["confirm_password"] = confirm_password
        response = self._transport.request("POST", "auth/reset-password/", json=payload)
        return parse_model(ResetPasswordResponse, response.data or {})

    def change_password(
        self,
        *,
        old_password: str,
        new_password: str,
        confirm_password: str,
        tenant_id: str | None = None,
    ) -> ChangePasswordResponse:
        """Change the password of the authenticated user.

        Endpoint: POST /api/v1/auth/change-password/
        """
        for label, value in (
            ("old_password", old_password),
            ("new_password", new_password),
            ("confirm_password", confirm_password),
        ):
            if not value or not isinstance(value, str):
                raise NovaValidationError(f"{label} must be a non-empty string.")
        response = self._transport.request(
            "POST",
            "auth/change-password/",
            json={
                "old_password": old_password,
                "new_password": new_password,
                "confirm_password": confirm_password,
            },
            tenant_id=tenant_id,
        )
        return parse_model(ChangePasswordResponse, response.data or {})

    @staticmethod
    def _reset_identity(uid: str, token: str) -> dict[str, Any]:
        if not uid or not isinstance(uid, str) or not uid.strip():
            raise NovaValidationError("uid must be a non-empty string.")
        if not token or not isinstance(token, str) or not token.strip():
            raise NovaValidationError("token must be a non-empty string.")
        return {"uid": uid.strip(), "token": token.strip()}

    def refresh(self, refresh_token: str) -> TokenRefresh:
        """Obtain a new access token using a valid refresh token.

        Endpoint: POST /api/v1/auth/refresh/

        Args:
            refresh_token: Valid JWT refresh token string.
        """
        if (
            not refresh_token
            or not isinstance(refresh_token, str)
            or not refresh_token.strip()
        ):
            raise NovaValidationError("refresh_token must be a non-empty string.")

        payload = {"refresh": refresh_token.strip()}
        response = self._transport.request("POST", "auth/refresh/", json=payload)
        return parse_model(TokenRefresh, response.data or {})

    def logout(self, refresh_token: str) -> Logout:
        """Invalidate refresh token via SimpleJWT blacklist.

        Endpoint: POST /api/v1/auth/logout/

        Args:
            refresh_token: Valid JWT refresh token string to invalidate.
        """
        if (
            not refresh_token
            or not isinstance(refresh_token, str)
            or not refresh_token.strip()
        ):
            raise NovaValidationError("refresh_token must be a non-empty string.")

        payload = {"refresh": refresh_token.strip()}
        response = self._transport.request("POST", "auth/logout/", json=payload)
        return parse_model(Logout, response.data or {})

    def me(self) -> UserMe:
        """Retrieve current authenticated user profile, tenant memberships, and active context.

        Endpoint: GET /api/v1/auth/me/
        """
        response = self._transport.request("GET", "auth/me/")
        return parse_model(UserMe, response.data or {})

    # Shortcut conveniences forwarding to api_keys sub-resource
    def list_api_keys(
        self,
        *,
        params: Mapping[str, Any] | None = None,
    ) -> PaginatedResponse[APIKey]:
        """Shortcut for client.auth.api_keys.list()."""
        return self.api_keys.list(params=params)

    def create_api_key(
        self,
        *,
        name: str = "Default API Key",
        expires_at: str | None = None,
    ) -> APIKeyCreate:
        """Shortcut for client.auth.api_keys.create()."""
        return self.api_keys.create(name=name, expires_at=expires_at)

    def revoke_api_key(self, api_key_id: str) -> None:
        """Shortcut for client.auth.api_keys.revoke()."""
        self.api_keys.revoke(api_key_id)
