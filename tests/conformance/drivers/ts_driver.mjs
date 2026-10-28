// Conformance driver for the TypeScript SDK: performs one abstract call and prints a normalised outcome.
import { pathToFileURL } from "node:url";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const dist = process.env.NOVA_CONF_TS_DIST ?? resolve(here, "../../../sdks/typescript/dist/index.js");
const sdk = await import(pathToFileURL(dist).href);

const CATEGORIES = [
  ["NovaRedirectError", "Redirect"], ["NovaRateLimitError", "RateLimit"], ["NovaAuthenticationError", "Authentication"],
  ["NovaPermissionError", "Permission"], ["NovaNotFoundError", "NotFound"], ["NovaValidationError", "Validation"],
  ["NovaServerError", "Server"], ["NovaAPIError", "API"], ["NovaTimeoutError", "Timeout"], ["NovaConnectionError", "Connection"],
];
function categorise(e) {
  for (const [cls, name] of CATEGORIES) if (e instanceof sdk[cls]) return name;
  return "Other:" + e?.constructor?.name;
}

const spec = JSON.parse(process.argv[2]);
const c = spec.client, call = spec.call;
const opts = { baseUrl: spec.base_url, retryBackoffMs: c.retry_backoff_ms ?? 1, retryJitter: false };
if ("api_key" in c) opts.apiKey = c.api_key;
if ("access_token" in c) opts.accessToken = c.access_token;
if ("tenant_id" in c) opts.tenantId = c.tenant_id;
if ("max_retries" in c) opts.maxRetries = c.max_retries;
if ("timeout_ms" in c) opts.timeoutMs = c.timeout_ms;

try {
  const nova = new sdk.NovaClient(opts);
  const ro = "tenant_id" in call ? { tenantId: call.tenant_id } : {};
  let data;
  switch (call.op) {
    case "health": data = { ...(await nova.health(ro)) }; break;
    case "templates.get": { const t = await nova.templates.get(call.id, ro); data = { id: t.id, name: t.name }; break; }
    case "templates.delete": await nova.templates.delete(call.id, ro); data = null; break;
    case "templates.create": {
      const body = { name: call.name };
      if ("subject" in call) body.subject = call.subject;
      await nova.templates.create(body, ro); data = null; break;
    }
    case "templates.list": {
      const q = {};
      for (const k of ["page", "page_size", "search"]) if (k in call) q[k] = call[k];
      const page = await nova.templates.list(q, ro);
      data = { ids: page.items.map((t) => t.id), has_next: page.hasNext };
      break;
    }
    case "templates.iter_all": {
      const page = await nova.templates.list({ page_size: call.page_size });
      const ids = [];
      for await (const t of page) ids.push(t.id);
      data = { ids };
      break;
    }
    default: throw new Error("unknown op " + call.op);
  }
  console.log(JSON.stringify({ kind: "ok", data }));
} catch (e) {
  if (!(e instanceof sdk.NovaError)) { console.error(e); process.exit(2); }
  const d = e.details;
  console.log(JSON.stringify({
    kind: "error", category: categorise(e), status: e.statusCode ?? null, code: e.errorCode ?? null,
    correlation_id: e.correlationId ?? null, retry_after: e.retryAfter ?? null,
    details_keys: d && typeof d === "object" && !Array.isArray(d) ? Object.keys(d).sort() : [],
    message: String(e.message) + " | " + String(e) + " | " + JSON.stringify(e),
  }));
}
