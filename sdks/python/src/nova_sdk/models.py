"""Core data models and envelope structures for Nova SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class EnvelopeMeta:
    """Metadata attached to Nova API responses."""

    timestamp: str | None = None
    correlation_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> EnvelopeMeta:
        if not data or not isinstance(data, dict):
            return cls()
        return cls(
            timestamp=data.get("timestamp"),
            correlation_id=data.get("correlation_id"),
            extra={
                k: v
                for k, v in data.items()
                if k not in ("timestamp", "correlation_id")
            },
        )


@dataclass
class PaginationInfo:
    """Pagination details for paginated list endpoints."""

    count: int = 0
    next: str | None = None
    previous: str | None = None
    page: int = 1
    total_pages: int = 1
    page_size: int = 20

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> PaginationInfo:
        if not data or not isinstance(data, dict):
            return cls()
        return cls(
            count=int(data.get("count", 0)),
            next=data.get("next"),
            previous=data.get("previous"),
            page=int(data.get("page", 1)),
            total_pages=int(data.get("total_pages", 1)),
            page_size=int(data.get("page_size", 20)),
        )


@dataclass
class ApiResponse(Generic[T]):
    """Standard unwrapped API response container."""

    data: T
    success: bool = True
    message: str = "Operation completed successfully."
    meta: EnvelopeMeta = field(default_factory=EnvelopeMeta)


@dataclass
class PaginatedResponse(Generic[T]):
    """Container for paginated results."""

    items: list[T]
    pagination: PaginationInfo
    meta: EnvelopeMeta = field(default_factory=EnvelopeMeta)

    @property
    def has_next(self) -> bool:
        """Whether the server reports another page after this one."""
        return self.pagination.next is not None

    def __iter__(self):
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> T:
        return self.items[index]

    @classmethod
    def from_response(
        cls,
        response: ApiResponse[Any],
        item_parser: Any = None,
    ) -> PaginatedResponse[T]:
        data = response.data
        if isinstance(data, dict) and "results" in data:
            raw_items = data.get("results") or []
            pagination = PaginationInfo.from_dict(data.get("pagination"))
        elif isinstance(data, list):
            raw_items = data
            pagination = PaginationInfo(
                count=len(raw_items),
                page=1,
                total_pages=1,
                page_size=len(raw_items) or 20,
            )
        else:
            raw_items = []
            pagination = PaginationInfo()

        if item_parser is not None and callable(item_parser):
            items = [item_parser(i) for i in raw_items]
        else:
            items = list(raw_items)

        return cls(items=items, pagination=pagination, meta=response.meta)


class Role:
    """Standard Nova tenant membership roles."""

    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    TEMPLATE_MANAGER = "TEMPLATE_MANAGER"
    CAMPAIGN_MANAGER = "CAMPAIGN_MANAGER"
    SENDER = "SENDER"
    VIEWER = "VIEWER"


class TenantStatus:
    """Standard Nova tenant organization lifecycle statuses."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class MembershipStatus:
    """Standard Nova tenant membership statuses."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class TemplateStatus:
    """Standard Nova email template lifecycle statuses."""

    ACTIVE = "ACTIVE"
    DRAFT = "DRAFT"
    ARCHIVED = "ARCHIVED"


class ContactStatus:
    """Standard Nova contact subscription statuses."""

    SUBSCRIBED = "SUBSCRIBED"
    UNSUBSCRIBED = "UNSUBSCRIBED"
    BOUNCED = "BOUNCED"


class EmailMessageStatus:
    """Standard Nova email message dispatch and delivery lifecycle statuses."""

    PENDING = "PENDING"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


class ProviderType:
    """Standard Nova email service provider integration types."""

    SMTP = "SMTP"
    AWS_SES = "AWS_SES"
    SENDGRID = "SENDGRID"
    MAILGUN = "MAILGUN"
    POSTMARK = "POSTMARK"
    MOCK = "MOCK"


class AuthenticationType:
    """Standard Nova provider authentication mechanisms."""

    BASIC = "BASIC"
    NONE = "NONE"
    OAUTH2 = "OAUTH2"


class WebhookEvent:
    """Standard Nova webhook event subscription choices."""

    # Contact events
    CONTACT_CREATED = "contact.created"
    CONTACT_DELETED = "contact.deleted"
    CONTACT_UPDATED = "contact.updated"

    # List events
    LIST_SUBSCRIBED = "list.subscribed"
    LIST_UNSUBSCRIBED = "list.unsubscribed"
    LIST_CONFIRMED = "list.confirmed"
    LIST_RESUBSCRIBED = "list.resubscribed"
    LIST_BOUNCED = "list.bounced"
    LIST_COMPLAINED = "list.complained"
    LIST_PENDING = "list.pending"
    LIST_REMOVED = "list.removed"

    # Segment events
    SEGMENT_JOINED = "segment.joined"
    SEGMENT_LEFT = "segment.left"

    # Email delivery events
    EMAIL_SENT = "email.sent"
    EMAIL_DELIVERED = "email.delivered"
    EMAIL_OPENED = "email.opened"
    EMAIL_CLICKED = "email.clicked"
    EMAIL_BOUNCED = "email.bounced"
    EMAIL_COMPLAINED = "email.complained"
    EMAIL_UNSUBSCRIBED = "email.unsubscribed"

    # Custom events
    CUSTOM_EVENT_CREATED = "custom_event.created"
    CUSTOM_EVENT_UPDATED = "custom_event.updated"
    CUSTOM_EVENT_DELETED = "custom_event.deleted"


class AccessLogCategory(str, Enum):
    """Activity classification categories for audit access logs."""

    AUTH = "AUTH"
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    UPLOAD = "UPLOAD"
    DOWNLOAD = "DOWNLOAD"
    EXPORT = "EXPORT"
    API_CALL = "API_CALL"
    SYSTEM = "SYSTEM"
