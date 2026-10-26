import {
  cleanCredential,
  hideCredential,
  normalizeTenantId,
  redact,
  resolveConfig,
  type NovaClientOptions,
  type NovaConfig,
} from "./config.js";
import { NovaValidationError } from "./errors.js";
import { HttpTransport, type RequestOptions } from "./http.js";
import { AuditResource } from "./resources/audit.js";
import { AnalyticsResource } from "./resources/analytics.js";
import { AssetsResource } from "./resources/assets.js";
import { AuthResource } from "./resources/auth.js";
import { CampaignsResource } from "./resources/campaigns.js";
import { ContactsResource } from "./resources/contacts.js";
import { EmailsResource } from "./resources/emails.js";
import { ProvidersResource } from "./resources/providers.js";
import { TemplatesResource } from "./resources/templates.js";
import { TenantsResource } from "./resources/tenants.js";
import { UsersResource } from "./resources/users.js";
import { WebhooksResource } from "./resources/webhooks.js";
import type { HealthStatus } from "./schemas.js";

const INSPECT = Symbol.for("nodejs.util.inspect.custom");

/**
 * Client for the Nova REST API.
 *
 * ```ts
 * const nova = new NovaClient({ apiKey: process.env.NOVA_API_KEY, tenantId: "…" });
 * const page = await nova.contacts.list({ page_size: 50 });
 * for await (const contact of page) console.log(contact.email);
 * ```
 *
 * Use it from server-side code. API keys and tokens are secrets and must never be
 * bundled into browser code; see the README.
 */
export class NovaClient {
  readonly auth: AuthResource;
  readonly users: UsersResource;
  readonly tenants: TenantsResource;
  readonly templates: TemplatesResource;
  readonly contacts: ContactsResource;
  readonly emails: EmailsResource;
  readonly providers: ProvidersResource;
  readonly webhooks: WebhooksResource;
  readonly analytics: AnalyticsResource;
  readonly campaigns: CampaignsResource;
  readonly audit: AuditResource;
  readonly assets: AssetsResource;

  private readonly transport: HttpTransport;

  constructor(options: NovaClientOptions = {}) {
    this.transport = new HttpTransport(resolveConfig(options));
    const http = this.transport;
    const resolveTenant = (explicit?: string): string => this.resolveTenant(explicit);

    this.auth = new AuthResource(http, (token) => this.setAccessToken(token));
    this.users = new UsersResource(http);
    this.tenants = new TenantsResource(http, resolveTenant);
    this.templates = new TemplatesResource(http);
    this.contacts = new ContactsResource(http);
    this.emails = new EmailsResource(http);
    this.providers = new ProvidersResource(http);
    this.webhooks = new WebhooksResource(http);
    this.analytics = new AnalyticsResource(http);
    this.campaigns = new CampaignsResource(http);
    this.audit = new AuditResource(http);
    this.assets = new AssetsResource(http);
  }

  /** The default tenant sent as `X-Tenant-ID`. */
  get tenantId(): string | undefined {
    return this.config.tenantId;
  }

  /** The resolved configuration (credentials are non-enumerable and never printed). */
  get config(): NovaConfig {
    return this.transport.config;
  }

  /** Low-level HTTP access, e.g. for endpoints newer than this SDK. */
  get http(): HttpTransport {
    return this.transport;
  }

  /**
   * Change the default tenant for this client. Because one client may serve many
   * concurrent requests, prefer {@link withTenant} or a per-call `tenantId` option.
   */
  setTenantId(tenantId: string | undefined): void {
    this.config.tenantId = tenantId ? normalizeTenantId(tenantId) : undefined;
  }

  /** Replace or clear the JWT access token. */
  setAccessToken(token: string | undefined): void {
    hideCredential(this.config, "accessToken", cleanCredential(token));
  }

  /** Replace or clear the API key. */
  setApiKey(apiKey: string | undefined): void {
    hideCredential(this.config, "apiKey", cleanCredential(apiKey));
  }

  /**
   * Return a new client scoped to another tenant. The original client is unchanged,
   * which makes this safe under concurrency (unlike {@link setTenantId}).
   */
  withTenant(tenantId: string): NovaClient {
    return this.withOptions({ tenantId });
  }

  /** Return a new client that inherits this client's configuration with overrides applied. */
  withOptions(overrides: NovaClientOptions): NovaClient {
    const c = this.config;
    return new NovaClient({
      baseUrl: c.baseUrl,
      apiKey: c.apiKey,
      accessToken: c.accessToken,
      tenantId: c.tenantId,
      timeoutMs: c.timeoutMs,
      maxRetries: c.maxRetries,
      retryBackoffMs: c.retryBackoffMs,
      retryJitter: c.retryJitter,
      defaultHeaders: c.defaultHeaders,
      fetch: c.fetch,
      dangerouslyAllowBrowser: true, // already validated when the parent was created
      ...overrides,
    });
  }

  /** `GET /api/v1/health/` */
  async health(options: RequestOptions = {}): Promise<HealthStatus> {
    const res = await this.transport.request<HealthStatus>("GET", "health/", options);
    return res.data;
  }

  /** Redacted description, safe to log. */
  toJSON(): Record<string, unknown> {
    const c = this.config;
    return {
      baseUrl: c.baseUrl,
      apiKey: redact(c.apiKey),
      accessToken: redact(c.accessToken),
      tenantId: c.tenantId ?? null,
    };
  }

  toString(): string {
    const d = this.toJSON();
    return `NovaClient(baseUrl=${String(d["baseUrl"])}, apiKey=${String(d["apiKey"])}, accessToken=${String(d["accessToken"])}, tenantId=${String(d["tenantId"])})`;
  }

  [INSPECT](): string {
    return this.toString();
  }

  private resolveTenant(explicit?: string): string {
    const tenant = explicit ?? this.config.tenantId;
    if (!tenant || !String(tenant).trim()) {
      throw new NovaValidationError("tenant_id must be provided or configured on the client.");
    }
    return normalizeTenantId(tenant);
  }
}
