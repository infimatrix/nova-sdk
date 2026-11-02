/**
 * Tenant lookup: an application that only knows the server URL and an API key must be able to call tenant-scoped
 * operations. When no tenant is named (argument or client default) the SDK asks the server which tenant the
 * credentials resolve to (GET auth/me/). Tenant deletion is never inferred.
 */
import { describe, expect, it } from "vitest";
import type { TemplateRenderResult, WebhookEndpointCreateUpdate } from "../src/index.js";
import { NovaValidationError } from "../src/index.js";
import { TENANT, envelope, mockClient, page } from "./helpers.js";

const path = (url: string) => new URL(url).pathname;
const OTHER = "22222222-2222-2222-2222-222222222222";

function server(currentTenant: unknown) {
  return (call: { url: string }) =>
    path(call.url) === "/api/v1/auth/me/"
      ? envelope({ email: "a@b.co", current_tenant: currentTenant })
      : path(call.url).endsWith("/members/")
        ? envelope(page([]))
        : envelope({ id: TENANT, name: "Acme" });
}

describe("tenant lookup", () => {
  it("looks the tenant up once and uses it in the path when none is configured", async () => {
    const { client, calls } = mockClient(server({ id: TENANT, name: "Acme" }));
    await client.tenants.listMembers();
    expect(calls.map((c) => `${c.method} ${path(c.url)}`)).toEqual([
      "GET /api/v1/auth/me/",
      `GET /api/v1/tenants/${TENANT}/members/`,
    ]);
    expect((await client.tenants.get()).name).toBe("Acme");
    expect(path(calls[calls.length - 1]!.url)).toBe(`/api/v1/tenants/${TENANT}/`);
  });

  it("does not call the server when a tenant is configured, and an explicit id wins", async () => {
    const { client, calls } = mockClient(server({ id: OTHER }), { tenantId: TENANT });
    expect(await client.tenants.currentTenantId()).toBe(TENANT);
    await client.tenants.listMembers();
    await client.tenants.listMembers(OTHER);
    expect(calls.map((c) => path(c.url))).toEqual([`/api/v1/tenants/${TENANT}/members/`, `/api/v1/tenants/${OTHER}/members/`]);
  });

  it("a client made with withTenant() uses that tenant without any lookup", async () => {
    const { client, calls } = mockClient(server({ id: OTHER }));
    await client.withTenant(TENANT).tenants.listMembers();
    expect(calls.map((c) => path(c.url))).toEqual([`/api/v1/tenants/${TENANT}/members/`]);
  });

  it.each([null, {}, { id: "" }])("fails clearly when the server reports no tenant (%j)", async (current) => {
    const { client } = mockClient(server(current));
    await expect(client.tenants.listMembers()).rejects.toBeInstanceOf(NovaValidationError);
    await expect(client.tenants.listMembers()).rejects.toThrow(/did not report a current tenant/);
  });

  it("validates the id the server reports", async () => {
    const { client, calls } = mockClient(server({ id: "../../etc" }));
    await expect(client.tenants.listMembers()).rejects.toBeInstanceOf(NovaValidationError);
    expect(calls.map((c) => path(c.url))).toEqual(["/api/v1/auth/me/"]); // nothing was requested with the bad id
  });

  it("never infers the id for tenant deletion, not even with a lookup request", async () => {
    const { client, calls } = mockClient(server({ id: TENANT }));
    await expect(client.tenants.delete()).rejects.toBeInstanceOf(NovaValidationError);
    expect(calls).toHaveLength(0);
  });
});

describe("corrected response types", () => {
  it("template render exposes subject and html_content as typed fields", async () => {
    const { client } = mockClient(() => envelope({ subject: "Hi Ada", html_content: "<p>Hi Ada</p>" }));
    const result: TemplateRenderResult = await client.templates.render(TENANT, { name: "Ada" });
    expect(result.subject).toBe("Hi Ada");
    expect(result.html_content).toBe("<p>Hi Ada</p>");
  });

  it("webhook creation exposes the signing secret as a typed field", async () => {
    const { client } = mockClient(() =>
      envelope({ id: TENANT, name: "w", url: "https://x.test/h", secret: "whsec_abc", secret_masked: "whsec_***", created_at: "2026-11-02T00:00:00Z" }),
    );
    const created: WebhookEndpointCreateUpdate = await client.webhooks.create({ name: "w", url: "https://x.test/h" });
    expect(created.secret).toBe("whsec_abc");
    expect(created.secret_masked).toBe("whsec_***");
  });
});
