"""Resource clients for Nova Python SDK."""

from nova_sdk.resources.analytics import AnalyticsResource
from nova_sdk.resources.assets import (
    AssetFilesResource,
    AssetFoldersResource,
    AssetsResource,
)
from nova_sdk.resources.audit import AccessLogsResource, AuditResource
from nova_sdk.resources.auth import APIKeysResource, AuthResource
from nova_sdk.resources.base import BaseResource
from nova_sdk.resources.campaigns import (
    CampaignsResource,
    TransactionalNotificationsResource,
)
from nova_sdk.resources.contacts import ContactGroupsResource, ContactsResource
from nova_sdk.resources.emails import EmailsResource
from nova_sdk.resources.providers import ProvidersResource
from nova_sdk.resources.templates import TemplatesResource
from nova_sdk.resources.tenants import TenantMembershipsResource, TenantsResource
from nova_sdk.resources.users import UsersResource
from nova_sdk.resources.webhooks import WebhooksResource

__all__ = [
    "APIKeysResource",
    "AccessLogsResource",
    "AssetFilesResource",
    "AssetFoldersResource",
    "AssetsResource",
    "AnalyticsResource",
    "AuditResource",
    "AuthResource",
    "BaseResource",
    "CampaignsResource",
    "ContactGroupsResource",
    "ContactsResource",
    "EmailsResource",
    "ProvidersResource",
    "TemplatesResource",
    "TenantMembershipsResource",
    "TenantsResource",
    "TransactionalNotificationsResource",
    "UsersResource",
    "WebhooksResource",
]
