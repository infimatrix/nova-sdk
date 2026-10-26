"""Asynchronous resource clients (generated from the synchronous resources)."""

from nova_sdk.aio.resources.analytics import AnalyticsResource
from nova_sdk.aio.resources.assets import (
    AssetFilesResource,
    AssetFoldersResource,
    AssetsResource,
)
from nova_sdk.aio.resources.audit import AccessLogsResource, AuditResource
from nova_sdk.aio.resources.auth import APIKeysResource, AuthResource
from nova_sdk.aio.resources.campaigns import (
    CampaignsResource,
    TransactionalNotificationsResource,
)
from nova_sdk.aio.resources.contacts import ContactGroupsResource, ContactsResource
from nova_sdk.aio.resources.emails import EmailsResource
from nova_sdk.aio.resources.providers import ProvidersResource
from nova_sdk.aio.resources.templates import TemplatesResource
from nova_sdk.aio.resources.tenants import TenantMembershipsResource, TenantsResource
from nova_sdk.aio.resources.users import UsersResource
from nova_sdk.aio.resources.webhooks import WebhooksResource

__all__ = [
    "APIKeysResource",
    "AccessLogsResource",
    "AnalyticsResource",
    "AssetFilesResource",
    "AssetFoldersResource",
    "AssetsResource",
    "AuditResource",
    "AuthResource",
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
