# Nova Python SDK

The official Python client library for **Nova — Dynamic Email Template & Email Delivery Platform**.

This SDK provides a secure, reliable interface to Nova's REST APIs, supporting multi-tenant email template management, variable rendering, transactional email delivery, provider integrations, and analytics.

---

## Features

- **Robust Authentication**: Supports both secure API keys (`Authorization: Bearer nova_key_...`) and SimpleJWT access tokens.
- **Tenant Context Management**: First-class support for multi-tenant workspaces via `X-Tenant-ID`, including scoped context managers (`with client.with_tenant(...)`).
- **Safety by Design**:
  - Non-idempotent operations (POST, PUT, PATCH, DELETE) are **never automatically retried**, preventing duplicate email dispatches or side effects.
  - Idempotent operations (GET, HEAD, OPTIONS) support configurable, bounded exponential backoff with jitter.
  - Secret sanitization: API keys and access tokens are strictly masked in `repr()`, logs, and exception tracebacks.
  - Cross-origin credential leakage is prevented by disabling automatic redirect following.
- **Envelope Unwrapping**: Automatically unwraps Nova's standard `{ success, message, data, meta }` response envelopes, while preserving correlation IDs for end-to-end observability.
- **Typed Models**: Responses are dataclass models (`tenant.name`) that also behave like read-only dicts (`tenant["name"]`); the untouched payload is always available as `model.raw`.
- **Sync and Async**: `NovaClient` (blocking) and `AsyncNovaClient` (`asyncio`) share the same resources, errors, and retry rules.
- **Pagination Helpers**: `iter_pages()` / `iter_items()` walk every page of any list endpoint.
- **Type Safety**: Built with complete type hints and PEP 561 compliance (`py.typed`).

---

## Installation

```bash
# Distributed through a private Google Cloud Artifact Registry repository (not PyPI):
pip install --index-url https://<LOCATION>-python.pkg.dev/<PROJECT>/<REPOSITORY>/simple/ infimatrix-nova-sdk
```

*(Requires Python 3.10+)*

---

## Quickstart

### 1. Client Initialization with API Key

```python
from nova_sdk import NovaClient

client = NovaClient(
    base_url="https://api.novamail.io",
    api_key="nova_key_your_api_key_here",
    tenant_id="00000000-0000-0000-0000-000000000001",
)

# Check platform health
health = client.health()
print(health)
# Output: {'status': 'ok', 'database': 'healthy'}

client.close()
```

### 2. Context Manager Usage (Recommended)

```python
from nova_sdk import NovaClient

with NovaClient(api_key="nova_key_...", tenant_id="...") as client:
    health = client.health()
    print("Nova API status:", health["status"])
```

### 3. Tenant Context Switching

```python
with NovaClient(api_key="nova_key_...") as client:
    # Operations in Tenant Alpha
    with client.with_tenant("11111111-1111-1111-1111-111111111111"):
        # Scoped to Tenant Alpha
        pass

    # Operations in Tenant Beta
    with client.with_tenant("22222222-2222-2222-2222-222222222222"):
        # Scoped to Tenant Beta
        pass
```

---

### 4. Async Usage

`AsyncNovaClient` exposes the same resources; every call is awaited.

```python
import asyncio
from nova_sdk.aio import AsyncNovaClient


async def main() -> None:
    async with AsyncNovaClient(api_key="nova_key_...") as client:
        page = await client.contacts.list(page_size=50)
        async for contact in client.iter_items(client.contacts.list):
            print(contact.email)


asyncio.run(main())
```

> One async client may serve many concurrent tasks. Prefer passing `tenant_id=...` per call over
> `set_tenant_id()`, which changes the default for every task sharing the client. `with_tenant()` is
> intentionally sync-only.

### 5. Typed Models

```python
tenant = client.tenants.get()
tenant.name  # attribute access with IDE completion
tenant["name"]  # dict-style access (backward compatible with 0.1.x)
tenant.get("slug")  # Mapping API
tenant.raw  # the exact JSON payload, including fields this SDK version does not know yet
```

All models live in `nova_sdk.schemas` and are generated from the Nova OpenAPI contract. Every field is
optional, so a newer server never breaks an older SDK.

### 6. Pagination

```python
from nova_sdk import iter_items, iter_pages

for contact in iter_items(client.contacts.list, search="acme", page_size=100):
    ...

for page in iter_pages(client.templates.list, page_size=50):
    print(page.pagination.page, "of", page.pagination.total_pages, len(page))

page = client.tenants.list()
if page.has_next:
    page = client.tenants.list(page=page.pagination.page + 1)
```

---

## Resource Clients

### Authentication & API Keys (`client.auth`)

```python
from nova_sdk import NovaClient

with NovaClient(base_url="https://api.novamail.io") as client:
    # 1. Login with credentials (optional set_current_token=True)
    session = client.auth.login(
        email="user@company.com",
        password="secure_password",
        set_current_token=True,
    )
    print("Logged in user:", session["user"]["email"])

    # 2. Get current authenticated user profile and memberships
    profile = client.auth.me()
    print("Current role:", profile["current_role"])

    # 3. API Key Management
    new_key = client.auth.create_api_key(name="CI Deployment Key")
    # Raw API key returned once upon creation:
    print("New key:", new_key["api_key"])

    # List active API keys
    keys = client.auth.list_api_keys()
    for k in keys:
        print(f"{k['name']} ({k['key_prefix']}...)")

    # Revoke an API key
    client.auth.revoke_api_key(new_key["id"])

    # 4. Refresh & Logout
    tokens = client.auth.refresh(refresh_token=session["refresh"])
    client.auth.logout(refresh_token=session["refresh"])
```

#### Registration and password recovery

```python
# Public endpoints (no credentials required)
session = client.auth.register(
    email="ada@example.com",
    password="a-strong-password",
    organization_name="Analytical Engines",
    set_current_token=True,
)

client.auth.forgot_password(
    "ada@example.com"
)  # sends the reset email (generic response)
client.auth.validate_reset_token(uid=uid, token=token)  # .valid -> bool
client.auth.reset_password(
    uid=uid, token=token, new_password="N3w-p4ssword!", confirm_password="N3w-p4ssword!"
)

# Authenticated
client.auth.change_password(
    old_password="...", new_password="...", confirm_password="..."
)
```

### Tenants & Memberships (`client.tenants`)

```python
from nova_sdk import NovaClient, Role, TenantStatus

with NovaClient(api_key="nova_key_...", base_url="https://api.novamail.io") as client:
    # 1. Create a new organization workspace
    tenant = client.tenants.create(
        name="Acme Corporation",
        slug="acme-corp",
        website="https://acme.com",
    )
    tenant_id = tenant["id"]

    # 2. List accessible workspaces
    for t in client.tenants.list():
        print(t["name"], t["slug"])

    # 3. Retrieve & update workspace details
    client.tenants.update(tenant_id, name="Acme Global")
    workspace = client.tenants.get(tenant_id)

    # 4. Manage Team Memberships
    # Add member
    member = client.tenants.add_member(
        tenant_id=tenant_id,
        email="developer@acme.com",
        role=Role.TEMPLATE_MANAGER,
    )

    # List members
    for m in client.tenants.list_members(tenant_id=tenant_id):
        print(m["user_email"], m["role"])

    # Update role
    client.tenants.update_member(
        membership_id=member["id"],
        tenant_id=tenant_id,
        role=Role.CAMPAIGN_MANAGER,
    )

    # Remove member
    client.tenants.remove_member(
        membership_id=member["id"],
        tenant_id=tenant_id,
    )
```

### Email Templates (`client.templates`)

```python
from nova_sdk import NovaClient, TemplateStatus

with NovaClient(api_key="nova_key_...", tenant_id="...") as client:
    # 1. Create a new email template with variable placeholders
    template = client.templates.create(
        name="Welcome Onboarding",
        subject="Welcome to Nova, {{ userName }}!",
        html_content="<h1>Welcome</h1><p>Hello {{ userName }}, thanks for joining!</p>",
        text_content="Hello {{ userName }}, thanks for joining!",
        status=TemplateStatus.ACTIVE,
        placeholders=[
            {"name": "userName", "default_value": "Valued User", "is_required": True}
        ],
    )
    template_id = template["id"]

    # 2. List templates with optional filtering and search
    for tpl in client.templates.list(status=TemplateStatus.ACTIVE, search="Welcome"):
        print(tpl["name"], tpl["slug"])

    # 3. Retrieve and update template
    client.templates.update(template_id, subject="Welcome aboard, {{ userName }}!")
    tpl_details = client.templates.get(template_id)

    # 4. Render template with variable substitution
    rendered = client.templates.render(template_id, variables={"userName": "Alex"})
    print("Rendered subject:", rendered["subject"])
    print("Rendered HTML:", rendered["html_content"])

    # 5. Archive or activate template shortcuts
    client.templates.archive(template_id)
    client.templates.activate(template_id)

    # 6. Delete template
    client.templates.delete(template_id)
```

### Contacts & Contact Groups (`client.contacts`)

```python
from nova_sdk import ContactStatus, NovaClient

with NovaClient(api_key="nova_key_...", tenant_id="...") as client:
    # 1. Create a new contact subscriber
    contact = client.contacts.create(
        email="developer@company.com",
        first_name="Alex",
        last_name="Rivers",
        phone_number="9876543210",
        country_code="+91",
        timezone="America/New_York",
        status=ContactStatus.SUBSCRIBED,
        metadata={"tier": "enterprise"},
    )
    contact_id = contact["id"]

    # 2. List and search contacts (supported filters: timezone, search, ordering, pagination)
    for c in client.contacts.list(search="Alex", timezone="America/New_York"):
        print(c["email"], c["first_name"], c["mobile_number"])

    # 3. Retrieve contact details & activity timeline
    contact_details = client.contacts.get(contact_id)
    activity = client.contacts.activity(contact_id)
    for event in activity:
        print(f"[{event['timestamp']}] {event['title']} - {event['status']}")

    # 4. Bulk operations
    # Download sample CSV format
    csv_sample = client.contacts.sample_template()

    # Bulk delete contacts
    client.contacts.bulk_delete([contact_id])

    # Bulk import from CSV (pass bytes, string, or a rewound file stream)
    # with open("contacts.csv", "rb") as f:
    #     client.contacts.bulk_upload(f)

    # 5. Manage Contact Groups
    group = client.contacts.create_group(
        name="Beta Testers",
        description="Users participating in beta testing programs",
    )
    group_id = group["id"]

    for g in client.contacts.list_groups():
        print(g["name"], g["id"])

    client.contacts.delete_group(group_id)
```

### Email Dispatch & Delivery Logs (`client.emails`)

> [!WARNING]
> **Dispatch Safety Notice**:
> Email dispatch operations (`send`, `bulk_send`, `group_send`) enqueue real email dispatches.
> Non-idempotent operations are **never automatically retried** by the SDK.
> If a request times out or a connection failure occurs, the dispatch task may have already succeeded on the server.
> Always check delivery logs via `client.emails.list_logs(...)` before manually resending to avoid sending duplicate emails to recipients.

```python
from nova_sdk import EmailMessageStatus, NovaClient

with NovaClient(api_key="nova_key_...", tenant_id="...") as client:
    # 1. Dispatch a single transactional email
    email = client.emails.send(
        recipient_email="user@example.com",
        subject="Welcome to Our Platform!",
        recipient_name="John Doe",
        sender_name="Nova Onboarding",
        sender_email="welcome@company.com",
        html_content="<h1>Welcome John!</h1><p>Thanks for signing up.</p>",
        text_content="Welcome John! Thanks for signing up.",
        note="User onboarding email",
    )
    print("Message ID:", email["message_id"], "Status:", email["status"])

    # 2. Batch dispatch using a template and contact list
    bulk_result = client.emails.bulk_send(
        template_id="33333333-3333-3333-3333-333333333333",
        contact_ids=[
            "55555555-5555-5555-5555-555555555555",
            "77777777-7777-7777-7777-777777777777",
        ],
        sender_email="news@company.com",
        fallback_variables={"first_name": "Valued Customer"},
    )
    print(bulk_result["message"], f"(Count: {bulk_result['count']})")

    # 3. Dispatch to an entire contact group
    group_result = client.emails.group_send(
        template_id="33333333-3333-3333-3333-333333333333",
        group_id="44444444-4444-4444-4444-444444444444",
        sender_email="announcements@company.com",
    )
    print(group_result["message"])

    # 4. List and filter delivery logs
    logs = client.emails.list_logs(
        status=EmailMessageStatus.DELIVERED,
        search="john",
        ordering="-created_at",
        page=1,
        page_size=20,
    )
    for log in logs:
        print(f"[{log['message_id']}] {log['receiver_email']} -> {log['status']}")

    # 5. Retrieve log detail & preview
    log_detail = client.emails.get_log(email["id"])
    preview = client.emails.preview(email["id"])
    print("Rendered HTML preview:", preview["html_content"])

    # 6. Export delivery logs as CSV (returns raw CSV text or bytes)
    csv_text = client.emails.export_csv(status=EmailMessageStatus.FAILED)
    with open("failed_deliveries.csv", "w", encoding="utf-8") as f:
        f.write(csv_text)
```

### Email Service Providers (`client.providers`)

Manage tenant-scoped external email delivery provider integrations (SMTP relays, Amazon SES, SendGrid, Mailgun) and dispatch verification test emails.

> [!WARNING]
> `client.providers.test()` triggers real email delivery asynchronously via Celery using the configured provider. Side-effect operations are never automatically retried by the SDK. Unit tests should always use mocks.

```python
from nova_sdk import AuthenticationType, NovaClient, ProviderType

with NovaClient(api_key="nova_key_...", tenant_id="...") as client:
    # 1. Inspect supported provider integration types
    supported_types = client.providers.types()
    for t in supported_types:
        print(f"[{t['key']}] {t['label']}: {t['description']}")

    # 2. Configure a new SMTP provider
    smtp_provider = client.providers.create(
        name="Production SMTP Relay",
        provider_type=ProviderType.SMTP,
        smtp_host="mail.example.com",
        smtp_port=587,
        tls_enabled=True,
        authentication_type=AuthenticationType.BASIC,
        smtp_user="mailer@example.com",
        smtp_password="secure_password",  # Write-only; never echoed back by API
        rate_limit_per_minute=50,
        senders=[
            {
                "name": "Support Team",
                "email": "support@example.com",
                "is_default": True,
            },
            {
                "name": "Billing",
                "email": "billing@example.com",
                "is_default": False,
            },
        ],
    )
    provider_id = smtp_provider["id"]

    # 3. Configure an Amazon SES provider
    ses_provider = client.providers.create(
        name="AWS SES Backup",
        provider_type=ProviderType.AWS_SES,
        aws_region="us-east-1",
        aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
        aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        priority=2,
    )

    # 4. List and filter providers (supports search, ordering, pagination)
    for p in client.providers.list(search="Production", ordering="priority"):
        print(f"{p['name']} ({p['provider_type']}) - active: {p['is_active']}")

    # 5. Retrieve provider details (credentials masked as boolean flags)
    details = client.providers.get(provider_id)
    print("Has password:", details["has_password"])
    print("Has secret key:", details["has_secret_key"])

    # 6. Update provider settings
    client.providers.update(
        provider_id,
        rate_limit_per_minute=100,
        is_active=True,
    )

    # 7. Dispatch a real verification test email
    test_result = client.providers.test(
        provider_id,
        recipient_email="admin@example.com",
    )
    print("Test email message ID:", test_result["message_id"])
    print("Background task ID:", test_result["task_id"])

    # 8. Delete provider configuration
    client.providers.delete(ses_provider["id"])
```

### Webhook Subscriptions (`client.webhooks`)

Manage tenant-scoped webhook subscriptions for real-time delivery event callbacks (`email.delivered`, `email.bounced`, `contact.created`, etc.), rotate HMAC signing secrets, and trigger test event dispatches.

> [!WARNING]
> `client.webhooks.rotate_secret()` immediately invalidates the previous HMAC signing key in the database.
> `client.webhooks.test()` dispatches a real test HTTP payload asynchronously via Celery to the configured callback URL. Side-effect operations are never automatically retried by the SDK. Unit tests should always use mocks.

```python
from nova_sdk import NovaClient, WebhookEvent

with NovaClient(api_key="nova_key_...", tenant_id="...") as client:
    # 1. Enumerate all supported webhook event choices
    available_events = client.webhooks.events()
    for ev in available_events:
        print(f"[{ev['key']}] {ev['label']}")

    # 2. Create a new webhook subscription
    webhook = client.webhooks.create(
        name="CRM Delivery Listener",
        url="https://crm.example.com/webhooks/nova",
        events=[
            WebhookEvent.EMAIL_DELIVERED,
            WebhookEvent.EMAIL_BOUNCED,
            WebhookEvent.EMAIL_OPENED,
        ],
        is_active=True,
    )
    webhook_id = webhook["id"]
    # Initial HMAC signing secret returned once on creation:
    print("HMAC Secret:", webhook["secret"])

    # 3. List and filter webhook subscriptions
    for sub in client.webhooks.list(search="crm.example.com"):
        print(f"{sub['name']} -> {sub['url']} ({len(sub['events'])} events)")

    # 4. Retrieve webhook detail (includes secret and secret_masked)
    detail = client.webhooks.get(webhook_id)
    print("Masked secret:", detail["secret_masked"])

    # 5. Update subscription settings or subscribed events
    client.webhooks.update(
        webhook_id,
        events=[WebhookEvent.EMAIL_DELIVERED, WebhookEvent.EMAIL_CLICKED],
        is_active=True,
    )

    # 6. Dispatch a real test event payload
    test_result = client.webhooks.test(
        webhook_id,
        event_type=WebhookEvent.EMAIL_DELIVERED,
    )
    print("Test task ID:", test_result["task_id"])

    # 7. Rotate HMAC signing key (invalidates previous secret)
    rotation = client.webhooks.rotate_secret(webhook_id)
    print("New rotated secret:", rotation["secret"])

    # 8. Delete subscription
    client.webhooks.delete(webhook_id)
```

### Transactional Campaigns (`client.campaigns`)

Manage tenant-scoped transactional email notification mappings and trigger verification test emails. Transactional notifications map external application event slugs (`welcome_email`, `password_reset`, `order_confirmation`) to Nova email templates.

Access via `client.campaigns.transactional` or convenient top-level shortcuts on `client.campaigns`.

> [!WARNING]
> `client.campaigns.transactional.send_test()` queues an actual email dispatch asynchronously via Celery.
> Side-effect operations (`create`, `update`, `delete`, and `send_test`) are strictly non-retryable (`allow_retry=False`) to prevent duplicate email dispatches. Unit tests must always mock these calls.

```python
from nova_sdk import NovaClient

with NovaClient(api_key="nova_key_...", tenant_id="...") as client:
    # 1. Create a new transactional notification mapping
    notif = client.campaigns.transactional.create(
        name="Welcome Onboarding Email",
        api_identifier="welcome_email",
        template_id="848bfbb9-f027-4a00-ab35-e14fc756f760",
        description="Triggered after a customer confirms their account",
    )
    notif_id = notif["id"]
    print(
        f"Created: {notif['display_id']} - {notif['name']} ({notif['api_identifier']})"
    )

    # 2. List notifications with pagination and search
    for item in client.campaigns.transactional.list(search="Welcome"):
        print(
            f"[{item['display_id']}] {item['name']} -> Template: {item['template_name']}"
        )

    # 3. Retrieve single notification
    detail = client.campaigns.transactional.get(notif_id)
    print("Notification details:", detail["api_identifier"])

    # 4. Partially update notification mapping
    client.campaigns.transactional.update(
        notif_id,
        name="Updated Welcome Onboarding Email",
        description="Updated trigger description",
    )

    # 5. Send a verification test email
    test_result = client.campaigns.transactional.send_test(
        notif_id,
        recipient_email="qa.tester@example.com",
        from_name="Nova Onboarding",
        sender_email="support@novamail.io",
        reply_to="support@novamail.io",
    )
    print("Test email message ID:", test_result["message_id"])

    # 6. Delete notification mapping
    client.campaigns.transactional.delete(notif_id)
```

### Analytics & Metrics (`client.analytics`)

```python
from datetime import date, timedelta
from nova_sdk import NovaClient

with NovaClient(api_key="nova_key_...", tenant_id="...") as client:
    # 1. Retrieve all-time dashboard overview metrics
    overview = client.analytics.dashboard()
    print("Total contacts:", overview["total_contacts"])
    print("Delivery funnel:", overview["email_overview"])
    # email_overview contains: total_email, sent, delivered, opened, clicked, bounced, complaint, failed

    # 2. Filter analytics by date range (supports strings, date, and datetime objects)
    today = date.today()
    last_week = today - timedelta(days=7)

    recent_metrics = client.analytics.dashboard(
        date_from=last_week,
        date_to=today,
    )
    print(
        "Emails delivered last 7 days:",
        recent_metrics["email_overview"]["delivered"],
    )

    # Inspect recently failed messages for debugging
    for failed in recent_metrics["recently_failed_messages"]:
        print(f"Failed to {failed['recipient_email']}: {failed['subject']}")
```

### Audit Access Logs (`client.audit`)

Audit access logs provide tenant-scoped observability and compliance tracking for all API requests and security events.

> [!NOTE]
> Access log querying requires active tenant membership (`IsTenantMember`). Viewing aggregate audit statistics (`stats()`) requires tenant administrator privileges (`IsTenantAdmin`).

```python
from datetime import datetime, timedelta, timezone
from nova_sdk import AccessLogCategory, NovaClient

with NovaClient(api_key="nova_key_...", tenant_id="...") as client:
    # 1. List access logs with rich filtering
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    logs = client.audit.access_logs.list(
        category=AccessLogCategory.API_CALL,
        status_code_gte=400,  # Filter client/server errors
        created_after=seven_days_ago,
        ordering="-created_at",
        page=1,
        page_size=25,
    )
    print(f"Total audit entries: {logs.pagination.count}")
    for entry in logs:
        print(
            f"[{entry['http_method']}] {entry['path']} -> {entry['status_code']} ({entry['ip_address']})"
        )

    # 2. Retrieve detailed access log record
    log_detail = client.audit.access_logs.get("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    print(
        f"Action: {log_detail['action']}, Response time: {log_detail['response_time_ms']}ms"
    )

    # 3. Retrieve audit log aggregate statistics (requires Tenant Admin role)
    stats = client.audit.access_logs.stats()
    print("Total logs:", stats["total"])
    print("Logs in last 24h:", stats["last_24h"])
    print("Category breakdown:", stats["category_breakdown"])
    print("Top users:", stats["top_users"])
    print("Average response time:", stats["avg_response_time_ms"], "ms")

    # Convenient top-level shortcuts are also available on client.audit:
    # client.audit.list(...)
    # client.audit.get(log_id)
    # client.audit.stats()
```

---

### Users (`client.users`)

```python
for user in client.users.list(page_size=50):
    print(user.email)

me = client.users.me()
print(me.current_role, me.current_tenant)
```

### Media Library (`client.assets`)

```python
folder = client.assets.folders.create(name="Brand")

asset = client.assets.files.upload("logo.png", folder=folder.id)  # path
asset = client.assets.files.upload(b"...", filename="banner.jpg")  # bytes
with open("report.pdf", "rb") as fh:
    asset = client.assets.files.upload(fh)  # binary stream

print(asset.public_url, asset.template_url)
client.assets.files.update(asset.id, name="Hero logo")
client.assets.files.delete(asset.id)
```

## Configuration

| Option | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `base_url` | `str` | `"http://localhost:8000"` | Nova API base URL (env: `NOVA_BASE_URL`) |
| `api_key` | `str` | `None` | Nova API key starting with `nova_key_` (env: `NOVA_API_KEY`) |
| `access_token` | `str` | `None` | JWT access token (env: `NOVA_ACCESS_TOKEN`) |
| `tenant_id` | `str` | `None` | Active tenant workspace UUID (env: `NOVA_TENANT_ID`) |
| `timeout` | `float` | `30.0` | Request timeout limit in seconds |
| `max_retries` | `int` | `3` | Maximum retry attempts for transient idempotent failures (capped at 10) |
| `retry_backoff_factor` | `float` | `0.5` | Exponential backoff multiplier |
| `retry_jitter` | `bool` | `True` | Adds randomized jitter to backoff intervals |
| `verify_ssl` | `bool` | `True` | Enforce HTTPS certificate verification |

---

## Error Handling

All SDK exceptions inherit from `NovaError`, exposing structured error information without leaking credentials:

```python
from nova_sdk import NovaClient
from nova_sdk.exceptions import (
    NovaAuthenticationError,
    NovaNotFoundError,
    NovaPermissionError,
    NovaRateLimitError,
    NovaValidationError,
)

with NovaClient(api_key="nova_key_...") as client:
    try:
        # Example call
        health = client.health()
    except NovaAuthenticationError as err:
        print("Invalid credentials:", err.message, err.correlation_id)
    except NovaPermissionError as err:
        print("Insufficient permissions for workspace:", err.message)
    except NovaNotFoundError as err:
        print("Resource not found:", err.message)
    except NovaRateLimitError as err:
        print(f"Rate limited. Retry after {err.retry_after} seconds.")
    except NovaValidationError as err:
        print("Invalid request parameters:", err.details)
```

---

## Compatibility

| SDK | Nova API | Python | Notes |
|-----|----------|--------|-------|
| 0.2.x | `/api/v1` (OpenAPI 1.0.0) | 3.10 - 3.14 | Typed models, async client, users/assets/account flows |
| 0.1.x | `/api/v1` | 3.10 - 3.14 | Dict responses |

### Migrating from 0.1.x

- Resource methods now return typed models instead of `dict`. Models implement `Mapping`, so
  `result["id"]`, `result.get("id")`, `"id" in result`, iteration and `result == {...}` keep working.
  `isinstance(result, dict)` is now `False`; use `dict(result)` or `result.to_dict()` when a real `dict` is required.
- `PaginatedResponse.items` contains models; `PaginatedResponse.has_next` was added.
- `nova_sdk.__version__` now lives in `nova_sdk._version` (still importable from `nova_sdk`).
- Email-log mutation endpoints (create/update/delete) are intentionally not exposed.

## Security Policy

- **No Secret Logging**: The client `__repr__` and config `__repr__` automatically redact secrets.
- **No Side-Effect Retries**: Non-idempotent operations (`POST`, `PUT`, `PATCH`, `DELETE`) will fail immediately on network or server error and will never create duplicate dispatches through blind retries.
- **Tenant Context Verification**: The server strictly enforces membership boundaries. Passing an unauthorized `X-Tenant-ID` is safely rejected by backend RBAC controls.
