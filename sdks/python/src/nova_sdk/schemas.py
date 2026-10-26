"""Typed response models for the Nova API.

AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_python_models.py.
Do not edit by hand; run the script to regenerate.

Every field is optional so that older/newer servers never break parsing;
the complete payload is always available as ``model.raw``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from nova_sdk._model_base import NovaModel

__all__ = [
    "APIKey",
    "APIKeyCreate",
    "AccessLog",
    "AccessLogStats",
    "AccessLogSummary",
    "AccessLogTopUser",
    "AssetFolder",
    "BulkContactDeleteResult",
    "BulkContactUploadResult",
    "ChangePasswordResponse",
    "Contact",
    "ContactActivity",
    "ContactGroup",
    "ContactSummary",
    "CurrentTenant",
    "DashboardAnalytics",
    "EmailBatchQueued",
    "EmailLog",
    "EmailOverview",
    "EmailPreview",
    "ForgotPasswordResponse",
    "HealthStatus",
    "HealthStatusDegraded",
    "Login",
    "Logout",
    "MediaAsset",
    "Membership",
    "MembershipCreate",
    "MembershipUpdate",
    "ProviderConfiguration",
    "ProviderConfigurationCreateUpdate",
    "ProviderTestDispatch",
    "ProviderTypeInfo",
    "RecentFailedMessage",
    "ResetPasswordResponse",
    "Sender",
    "Template",
    "TemplatePlaceholder",
    "TemplateRender",
    "Tenant",
    "TenantCreate",
    "TenantMembershipSummary",
    "TenantUpdate",
    "TokenRefresh",
    "TransactionalNotification",
    "TransactionalTestDispatch",
    "User",
    "UserMe",
    "UserRegister",
    "ValidateResetTokenResponse",
    "WebhookEndpoint",
    "WebhookEndpointCreateUpdate",
    "WebhookEventChoice",
    "WebhookSecretRotation",
    "WebhookTestDispatch",
]


@dataclass(eq=False)
class APIKey(NovaModel):
    """Serializer for listing and reading user API Key records (without exposing raw secret key)."""

    id: str | None = None
    name: str | None = None
    key_prefix: str | None = None
    is_active: bool | None = None
    created_at: str | None = None
    expires_at: str | None = None
    last_used_at: str | None = None


@dataclass(eq=False)
class APIKeyCreate(NovaModel):
    """Serializer for creating a new API Key for the authenticated user."""

    id: str | None = None
    name: str | None = None
    key_prefix: str | None = None
    api_key: str | None = None
    is_active: bool | None = None
    expires_at: str | None = None
    created_at: str | None = None


@dataclass(eq=False)
class AccessLog(NovaModel):
    """Read-only serializer for access log entries."""

    id: str | None = None
    workspace_name: str | None = None
    user: str | None = None
    user_email: str | None = None
    user_name: str | None = None
    created_by: str | None = None
    client_code: str | None = None
    category: str | None = None
    category_display: str | None = None
    action: str | None = None
    description: str | None = None
    http_method: str | None = None
    path: str | None = None
    query_string: str | None = None
    status_code: int | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    response_time_ms: int | None = None
    metadata: Any | None = None
    created_at: str | None = None


@dataclass(eq=False)
class AccessLogStats(NovaModel):
    """AccessLogStats response model."""

    _nested: ClassVar[dict[str, tuple[str, bool]]] = {
        "top_users": ("AccessLogTopUser", True),
    }

    total: int | None = None
    last_24h: int | None = None
    last_7d: int | None = None
    category_breakdown: dict[str, Any] | None = None
    top_users: list[AccessLogTopUser] | None = None
    avg_response_time_ms: float | None = None


@dataclass(eq=False)
class AccessLogSummary(NovaModel):
    """Compact serializer for access log list views."""

    id: str | None = None
    workspace_name: str | None = None
    ip_address: str | None = None
    client_code: str | None = None
    action: str | None = None
    created_by: str | None = None
    created_at: str | None = None
    category: str | None = None
    category_display: str | None = None
    http_method: str | None = None
    path: str | None = None
    status_code: int | None = None
    response_time_ms: int | None = None


@dataclass(eq=False)
class AccessLogTopUser(NovaModel):
    """AccessLogTopUser response model."""

    user__email: str | None = None
    activity_count: int | None = None


@dataclass(eq=False)
class AssetFolder(NovaModel):
    """AssetFolder response model."""

    id: str | None = None
    name: str | None = None
    slug: str | None = None
    file_count: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(eq=False)
class BulkContactDeleteResult(NovaModel):
    """BulkContactDeleteResult response model."""

    success: bool | None = None
    deleted_count: int | None = None


@dataclass(eq=False)
class BulkContactUploadResult(NovaModel):
    """BulkContactUploadResult response model."""

    _nested: ClassVar[dict[str, tuple[str, bool]]] = {
        "contacts": ("Contact", True),
    }

    message: str | None = None
    created_count: int | None = None
    errors: list[dict[str, Any]] | None = None
    contacts: list[Contact] | None = None


@dataclass(eq=False)
class ChangePasswordResponse(NovaModel):
    """ChangePasswordResponse response model."""

    detail: str | None = None
    message: str | None = None


@dataclass(eq=False)
class Contact(NovaModel):
    """Contact response model."""

    id: str | None = None
    user_id: str | None = None
    contact_id_str: str | None = None
    username: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    country_code: str | None = None
    phone_number: str | None = None
    mobile_number: str | None = None
    timezone: str | None = None
    status: str | None = None
    metadata: Any | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(eq=False)
class ContactActivity(NovaModel):
    """ContactActivity response model."""

    id: str | None = None
    title: str | None = None
    subject: str | None = None
    status: str | None = None
    timestamp: str | None = None


@dataclass(eq=False)
class ContactGroup(NovaModel):
    """ContactGroup response model."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    contacts: list[str] | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(eq=False)
class ContactSummary(NovaModel):
    """ContactSummary response model."""

    id: str | None = None
    user_id: str | None = None
    contact_id_str: str | None = None
    username: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    country_code: str | None = None
    phone_number: str | None = None
    mobile_number: str | None = None
    timezone: str | None = None
    status: str | None = None
    created_at: str | None = None


@dataclass(eq=False)
class CurrentTenant(NovaModel):
    """Shape of the active tenant context (documentation of ``UserMe.current_tenant``)."""

    id: str | None = None
    name: str | None = None
    slug: str | None = None
    website: str | None = None
    logo_url: str | None = None


@dataclass(eq=False)
class DashboardAnalytics(NovaModel):
    """DashboardAnalytics response model."""

    _nested: ClassVar[dict[str, tuple[str, bool]]] = {
        "email_overview": ("EmailOverview", False),
        "recently_added_contacts": ("ContactSummary", True),
        "recently_failed_messages": ("RecentFailedMessage", True),
    }

    total_contacts: int | None = None
    new_contacts: int | None = None
    email_overview: EmailOverview | None = None
    recently_added_contacts: list[ContactSummary] | None = None
    recently_failed_messages: list[RecentFailedMessage] | None = None


@dataclass(eq=False)
class EmailBatchQueued(NovaModel):
    """EmailBatchQueued response model."""

    message: str | None = None
    count: int | None = None


@dataclass(eq=False)
class EmailLog(NovaModel):
    """EmailLog response model."""

    id: str | None = None
    message_id: str | None = None
    sender_name: str | None = None
    sender_email: str | None = None
    receiver_name: str | None = None
    receiver_email: str | None = None
    template_name: str | None = None
    subject: str | None = None
    note: str | None = None
    status: str | None = None
    created_at: str | None = None


@dataclass(eq=False)
class EmailOverview(NovaModel):
    """EmailOverview response model."""

    total_email: int | None = None
    sent: int | None = None
    delivered: int | None = None
    opened: int | None = None
    clicked: int | None = None
    bounced: int | None = None
    complaint: int | None = None
    failed: int | None = None


@dataclass(eq=False)
class EmailPreview(NovaModel):
    """EmailPreview response model."""

    id: str | None = None
    message_id: str | None = None
    sender_name: str | None = None
    sender_email: str | None = None
    receiver_name: str | None = None
    receiver_email: str | None = None
    template_name: str | None = None
    subject: str | None = None
    note: str | None = None
    status: str | None = None
    created_at: str | None = None
    html_content: str | None = None
    text_content: str | None = None
    metadata: Any | None = None


@dataclass(eq=False)
class ForgotPasswordResponse(NovaModel):
    """ForgotPasswordResponse response model."""

    detail: str | None = None
    message: str | None = None


@dataclass(eq=False)
class HealthStatus(NovaModel):
    """HealthStatus response model."""

    status: str | None = None
    database: str | None = None


@dataclass(eq=False)
class HealthStatusDegraded(NovaModel):
    """HealthStatusDegraded response model."""

    status: str | None = None
    database: str | None = None


@dataclass(eq=False)
class Login(NovaModel):
    """Login response model."""

    _nested: ClassVar[dict[str, tuple[str, bool]]] = {
        "user": ("User", False),
        "tenants": ("TenantMembershipSummary", True),
    }

    access: str | None = None
    refresh: str | None = None
    user: User | None = None
    tenants: list[TenantMembershipSummary] | None = None


@dataclass(eq=False)
class Logout(NovaModel):
    """Logout response model."""

    refresh: str | None = None


@dataclass(eq=False)
class MediaAsset(NovaModel):
    """MediaAsset response model."""

    id: str | None = None
    folder: str | None = None
    folder_name: str | None = None
    name: str | None = None
    file: str | None = None
    file_size: int | None = None
    formatted_file_size: str | None = None
    mime_type: str | None = None
    public_url: str | None = None
    template_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(eq=False)
class Membership(NovaModel):
    """Membership response model."""

    id: str | None = None
    user_id: str | None = None
    user_email: str | None = None
    user_first_name: str | None = None
    user_last_name: str | None = None
    role: str | None = None
    status: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(eq=False)
class MembershipCreate(NovaModel):
    """MembershipCreate response model."""

    role: str | None = None
    status: str | None = None


@dataclass(eq=False)
class MembershipUpdate(NovaModel):
    """MembershipUpdate response model."""

    role: str | None = None
    status: str | None = None


@dataclass(eq=False)
class ProviderConfiguration(NovaModel):
    """ProviderConfiguration response model."""

    _nested: ClassVar[dict[str, tuple[str, bool]]] = {
        "senders": ("Sender", True),
    }

    id: str | None = None
    name: str | None = None
    provider_type: str | None = None
    senders: list[Sender] | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    tls_enabled: bool | None = None
    authentication_type: str | None = None
    smtp_user: str | None = None
    has_password: bool | None = None
    aws_region: str | None = None
    aws_access_key_id: str | None = None
    has_secret_key: bool | None = None
    rate_limit_per_minute: int | None = None
    is_active: bool | None = None
    priority: int | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(eq=False)
class ProviderConfigurationCreateUpdate(NovaModel):
    """ProviderConfigurationCreateUpdate response model."""

    _nested: ClassVar[dict[str, tuple[str, bool]]] = {
        "senders": ("Sender", True),
    }

    id: str | None = None
    name: str | None = None
    provider_type: str | None = None
    senders: list[Sender] | None = None
    smtp_host: str | None = None
    smtp_port: int | None = None
    tls_enabled: bool | None = None
    authentication_type: str | None = None
    smtp_user: str | None = None
    aws_region: str | None = None
    aws_access_key_id: str | None = None
    rate_limit_per_minute: int | None = None
    is_active: bool | None = None
    priority: int | None = None
    encrypted_credentials: Any | None = None


@dataclass(eq=False)
class ProviderTestDispatch(NovaModel):
    """ProviderTestDispatch response model."""

    success: bool | None = None
    message: str | None = None
    message_id: str | None = None
    task_id: str | None = None


@dataclass(eq=False)
class ProviderTypeInfo(NovaModel):
    """ProviderTypeInfo response model."""

    key: str | None = None
    label: str | None = None
    description: str | None = None


@dataclass(eq=False)
class RecentFailedMessage(NovaModel):
    """RecentFailedMessage response model."""

    id: str | None = None
    recipient_email: str | None = None
    subject: str | None = None
    status: str | None = None
    metadata: Any | None = None
    created_at: str | None = None


@dataclass(eq=False)
class ResetPasswordResponse(NovaModel):
    """ResetPasswordResponse response model."""

    detail: str | None = None
    message: str | None = None


@dataclass(eq=False)
class Sender(NovaModel):
    """Sender response model."""

    name: str | None = None
    email: str | None = None
    is_default: bool | None = None


@dataclass(eq=False)
class Template(NovaModel):
    """Template response model."""

    _nested: ClassVar[dict[str, tuple[str, bool]]] = {
        "placeholders": ("TemplatePlaceholder", True),
    }

    id: str | None = None
    name: str | None = None
    slug: str | None = None
    subject: str | None = None
    description: str | None = None
    status: str | None = None
    action_types: Any | None = None
    design_config: Any | None = None
    html_content: str | None = None
    text_content: str | None = None
    placeholders: list[TemplatePlaceholder] | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(eq=False)
class TemplatePlaceholder(NovaModel):
    """TemplatePlaceholder response model."""

    id: int | None = None
    name: str | None = None
    default_value: str | None = None
    is_required: bool | None = None


@dataclass(eq=False)
class TemplateRender(NovaModel):
    """TemplateRender response model."""

    variables: dict[str, Any] | None = None


@dataclass(eq=False)
class Tenant(NovaModel):
    """Tenant response model."""

    id: str | None = None
    name: str | None = None
    slug: str | None = None
    website: str | None = None
    logo_url: str | None = None
    status: str | None = None
    is_active: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(eq=False)
class TenantCreate(NovaModel):
    """TenantCreate response model."""

    id: str | None = None
    name: str | None = None
    slug: str | None = None
    website: str | None = None
    logo_url: str | None = None
    status: str | None = None


@dataclass(eq=False)
class TenantMembershipSummary(NovaModel):
    """TenantMembershipSummary response model."""

    id: str | None = None
    name: str | None = None
    slug: str | None = None
    website: str | None = None
    logo_url: str | None = None
    role: str | None = None


@dataclass(eq=False)
class TenantUpdate(NovaModel):
    """TenantUpdate response model."""

    name: str | None = None
    website: str | None = None
    logo_url: str | None = None
    status: str | None = None


@dataclass(eq=False)
class TokenRefresh(NovaModel):
    """TokenRefresh response model."""

    access: str | None = None
    refresh: str | None = None


@dataclass(eq=False)
class TransactionalNotification(NovaModel):
    """TransactionalNotification response model."""

    id: str | None = None
    display_id: str | None = None
    name: str | None = None
    api_identifier: str | None = None
    template_id: str | None = None
    template_name: str | None = None
    description: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(eq=False)
class TransactionalTestDispatch(NovaModel):
    """TransactionalTestDispatch response model."""

    message: str | None = None
    message_id: str | None = None
    email_id: str | None = None


@dataclass(eq=False)
class User(NovaModel):
    """User response model."""

    id: str | None = None
    email: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None
    is_staff: bool | None = None
    is_superuser: bool | None = None
    created_at: str | None = None


@dataclass(eq=False)
class UserMe(NovaModel):
    """UserMe response model."""

    _nested: ClassVar[dict[str, tuple[str, bool]]] = {
        "tenants": ("TenantMembershipSummary", True),
        "current_tenant": ("CurrentTenant", False),
    }

    id: str | None = None
    email: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None
    is_staff: bool | None = None
    is_superuser: bool | None = None
    created_at: str | None = None
    tenants: list[TenantMembershipSummary] | None = None
    current_tenant: CurrentTenant | None = None
    current_role: str | None = None


@dataclass(eq=False)
class UserRegister(NovaModel):
    """UserRegister response model."""

    _nested: ClassVar[dict[str, tuple[str, bool]]] = {
        "user": ("User", False),
        "tenants": ("TenantMembershipSummary", True),
    }

    access: str | None = None
    refresh: str | None = None
    user: User | None = None
    tenants: list[TenantMembershipSummary] | None = None


@dataclass(eq=False)
class ValidateResetTokenResponse(NovaModel):
    """ValidateResetTokenResponse response model."""

    valid: bool | None = None
    detail: str | None = None


@dataclass(eq=False)
class WebhookEndpoint(NovaModel):
    """WebhookEndpoint response model."""

    id: str | None = None
    name: str | None = None
    url: str | None = None
    secret: str | None = None
    secret_masked: str | None = None
    events: Any | None = None
    is_active: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass(eq=False)
class WebhookEndpointCreateUpdate(NovaModel):
    """WebhookEndpointCreateUpdate response model."""

    id: str | None = None
    name: str | None = None
    url: str | None = None
    events: list[str] | None = None
    is_active: bool | None = None


@dataclass(eq=False)
class WebhookEventChoice(NovaModel):
    """WebhookEventChoice response model."""

    key: str | None = None
    label: str | None = None


@dataclass(eq=False)
class WebhookSecretRotation(NovaModel):
    """WebhookSecretRotation response model."""

    secret: str | None = None
    message: str | None = None


@dataclass(eq=False)
class WebhookTestDispatch(NovaModel):
    """WebhookTestDispatch response model."""

    success: bool | None = None
    message: str | None = None
    webhook_id: str | None = None
    task_id: str | None = None
    url: str | None = None
    event_type: str | None = None
