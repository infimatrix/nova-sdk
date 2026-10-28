"""Conformance driver for the Python SDK: performs one abstract call and prints a normalised outcome."""

import json
import sys

from nova_sdk import NovaClient
from nova_sdk import exceptions as ex
from nova_sdk.pagination import iter_items

CATEGORIES = [  # most specific first
    (ex.NovaRedirectError, "Redirect"),
    (ex.NovaRateLimitError, "RateLimit"),
    (ex.NovaAuthenticationError, "Authentication"),
    (ex.NovaPermissionError, "Permission"),
    (ex.NovaNotFoundError, "NotFound"),
    (ex.NovaValidationError, "Validation"),
    (ex.NovaServerError, "Server"),
    (ex.NovaAPIError, "API"),
    (ex.NovaTimeoutError, "Timeout"),
    (ex.NovaConnectionError, "Connection"),
]


def categorise(error):
    for cls, name in CATEGORIES:
        if isinstance(error, cls):
            return name
    return "Other:" + type(error).__name__


def main():
    spec = json.loads(sys.argv[1])
    c, call = spec["client"], spec["call"]
    kwargs = {"base_url": spec["base_url"], "retry_backoff_factor": c.get("retry_backoff_ms", 1) / 1000, "retry_jitter": False}
    for src, dst in (("api_key", "api_key"), ("access_token", "access_token"), ("tenant_id", "tenant_id"), ("max_retries", "max_retries")):
        if src in c:
            kwargs[dst] = c[src]
    if "timeout_ms" in c:
        kwargs["timeout"] = c["timeout_ms"] / 1000
    try:
        with NovaClient(**kwargs) as nova:
            op = call["op"]
            tenant = {"tenant_id": call["tenant_id"]} if "tenant_id" in call else {}
            if op == "health":
                data = nova.health()
                data = dict(data)
            elif op == "templates.get":
                t = nova.templates.get(call["id"], **tenant)
                data = {"id": t.id, "name": t.name}
            elif op == "templates.delete":
                nova.templates.delete(call["id"], **tenant)
                data = None
            elif op == "templates.create":
                extra = {k: call[k] for k in ("subject",) if k in call}
                nova.templates.create(name=call["name"], **extra, **tenant)
                data = None
            elif op == "templates.list":
                q = {k: call[k] for k in ("page", "page_size", "search") if k in call}
                page = nova.templates.list(**q)
                data = {"ids": [t.id for t in page], "has_next": page.has_next}
            elif op == "templates.iter_all":
                data = {"ids": [t.id for t in iter_items(nova.templates.list, page_size=call["page_size"])]}
            else:
                raise SystemExit(f"unknown op {op}")
        print(json.dumps({"kind": "ok", "data": data}))
    except ex.NovaError as e:
        details = getattr(e, "details", None)
        print(json.dumps({
            "kind": "error",
            "category": categorise(e),
            "status": e.status_code,
            "code": e.error_code,
            "correlation_id": getattr(e, "correlation_id", None),
            "retry_after": getattr(e, "retry_after", None),
            "details_keys": sorted(details) if isinstance(details, dict) else [],
            "message": str(e) + " | " + repr(e),
        }))


main()
