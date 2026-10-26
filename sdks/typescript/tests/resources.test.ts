import { describe, expect, it } from "vitest";
import { NovaClient, NovaNotFoundError, NovaValidationError } from "../src/index.js";
import { TENANT, envelope, errorEnvelope, mockClient, page } from "./helpers.js";

const path = (url: string) => new URL(url).pathname;
const query = (url: string) => Object.fromEntries(new URL(url).searchParams);
const ID = "33333333-3333-3333-3333-333333333333";

describe("auth", () => {
  it("login posts credentials and can store the token", async () => {
    const { client, calls } = mockClient(() => envelope({ access: "jwt-1", refresh: "r-1", user: {}, tenants: [] }));
    const result = await client.auth.login({ email: " a@b.co ", password: "pw" }, { setCurrentToken: true });
    expect(result.access).toBe("jwt-1");
    expect(path(calls[0]!.url)).toBe("/api/v1/auth/login/");
    expect(calls[0]?.body).toEqual({ email: "a@b.co", password: "pw" });

    client.setApiKey(undefined);
    await client.auth.me();
    expect(calls[1]?.headers["Authorization"]).toBe("Bearer jwt-1");
  });

  it("validates required login fields client-side", async () => {
    const { client, calls } = mockClient(() => envelope({}));
    await expect(client.auth.login({ email: "", password: "x" })).rejects.toBeInstanceOf(NovaValidationError);
    await expect(client.auth.login({ email: "a@b.co", password: "" })).rejects.toBeInstanceOf(NovaValidationError);
    expect(calls).toHaveLength(0);
  });

  it("register, refresh and logout", async () => {
    const { client, calls } = mockClient(() => envelope({ access: "jwt", refresh: "r" }, { status: 201 }));
    await client.auth.register({ email: "n@e.co", password: "Str0ng-Passw0rd!", organization_name: "Acme" });
    expect(calls[0]?.body).toEqual({ email: "n@e.co", password: "Str0ng-Passw0rd!", organization_name: "Acme" });
    await client.auth.refresh("r1");
    expect(calls[1]?.body).toEqual({ refresh: "r1" });
    await client.auth.logout("r1");
    expect(path(calls[2]!.url)).toBe("/api/v1/auth/logout/");
  });

  it("password recovery flows", async () => {
    const { client, calls } = mockClient(() => envelope({ detail: "ok", message: "ok", valid: true }));
    await client.auth.forgotPassword(" a@b.co ");
    expect(calls[0]?.body).toEqual({ email: "a@b.co" });
    expect((await client.auth.validateResetToken({ uid: "u", token: "t" })).valid).toBe(true);
    await client.auth.resetPassword({ uid: "u", token: "t", new_password: "N3w-Passw0rd!x", confirm_password: "N3w-Passw0rd!x" });
    expect(calls[2]?.body).toEqual({ uid: "u", token: "t", new_password: "N3w-Passw0rd!x", confirm_password: "N3w-Passw0rd!x" });
    await client.auth.changePassword({ old_password: "o", new_password: "n", confirm_password: "n" });
    expect(path(calls[3]!.url)).toBe("/api/v1/auth/change-password/");
    await expect(client.auth.resetPassword({ token: "t", new_password: "x" })).rejects.toBeInstanceOf(NovaValidationError);
  });

  it("accepts uidb64 as the user identifier", async () => {
    const { client, calls } = mockClient(() => envelope({}));
    await client.auth.resetPassword({ uidb64: "abc", token: "t", new_password: "pw" });
    expect((calls[0]?.body as Record<string, unknown>)["uid"]).toBe("abc");
  });

  it("API keys: list, create, revoke", async () => {
    const { client, calls } = mockClient((call) =>
      call.method === "GET" ? envelope(page([{ id: "k1" }])) : envelope({ api_key: "nova_key_new" }, { status: 201 }),
    );
    expect((await client.auth.apiKeys.list({ page_size: 5 })).items).toHaveLength(1);
    expect(query(calls[0]!.url)).toEqual({ page_size: "5" });
    expect((await client.auth.apiKeys.create({})).api_key).toBe("nova_key_new");
    expect(calls[1]?.body).toEqual({ name: "Default API Key" });
    await client.auth.apiKeys.revoke(ID);
    expect(calls[2]).toMatchObject({ method: "DELETE" });
  });
});

describe("tenants", () => {
  it("CRUD with the default tenant", async () => {
    const { client, calls } = mockClient(() => envelope({ id: TENANT }), { tenantId: TENANT });
    await client.tenants.get();
    expect(path(calls[0]!.url)).toBe(`/api/v1/tenants/${TENANT}/`);
    await client.tenants.update({ name: "New" });
    expect(calls[1]).toMatchObject({ method: "PATCH", body: { name: "New" } });
    await client.tenants.create({ name: "A", slug: "a" });
    await client.tenants.delete();
    expect(calls[3]).toMatchObject({ method: "DELETE" });
  });

  it("requires a tenant for tenant-scoped paths", async () => {
    const { client } = mockClient(() => envelope({}));
    await expect(client.tenants.get()).rejects.toThrow(/tenant_id must be provided/);
    await expect(client.tenants.get("nope")).rejects.toBeInstanceOf(NovaValidationError);
  });

  it("memberships", async () => {
    const { client, calls } = mockClient((call) => (call.method === "GET" && !call.url.includes(ID) ? envelope(page([{ id: ID }])) : envelope({ id: ID })), {
      tenantId: TENANT,
    });
    expect((await client.tenants.listMembers()).items).toHaveLength(1);
    expect(path(calls[0]!.url)).toBe(`/api/v1/tenants/${TENANT}/members/`);
    await client.tenants.addMember({ email: "x@y.co", role: "VIEWER" });
    await client.tenants.getMember(ID);
    await client.tenants.updateMember(ID, { role: "SENDER" });
    await client.tenants.removeMember(ID);
    expect(calls.map((c) => c.method)).toEqual(["GET", "POST", "GET", "PATCH", "DELETE"]);
    await expect(client.tenants.updateMember(ID, {})).rejects.toBeInstanceOf(NovaValidationError);
  });
});

describe("contacts", () => {
  it("lists with filters and manages contacts and groups", async () => {
    const { client, calls } = mockClient((call) => (call.method === "GET" && call.url.endsWith("/") ? envelope(page([])) : envelope({ id: ID })));
    await client.contacts.list({ search: "a", timezone: "UTC", page_size: 10 });
    expect(query(calls[0]!.url)).toEqual({ search: "a", timezone: "UTC", page_size: "10" });
    await client.contacts.create({ email: "a@b.co" });
    await client.contacts.update(ID, { first_name: "Ada" });
    await client.contacts.delete(ID);
    await client.contacts.groups.create({ name: "VIP" });
    await client.contacts.groups.update(ID, { name: "VIPs" });
    await client.contacts.groups.delete(ID);
    expect(calls.slice(1).map((c) => `${c.method} ${path(c.url)}`)).toEqual([
      "POST /api/v1/contacts/",
      `PATCH /api/v1/contacts/${ID}/`,
      `DELETE /api/v1/contacts/${ID}/`,
      "POST /api/v1/contacts/groups/",
      `PATCH /api/v1/contacts/groups/${ID}/`,
      `DELETE /api/v1/contacts/groups/${ID}/`,
    ]);
  });

  it("bulk delete validates and sends ids", async () => {
    const { client, calls } = mockClient(() => envelope({ success: true, deleted_count: 2 }));
    await expect(client.contacts.bulkDelete([])).rejects.toBeInstanceOf(NovaValidationError);
    expect((await client.contacts.bulkDelete([" a ", "b"])).deleted_count).toBe(2);
    expect(calls[0]?.body).toEqual({ contact_ids: ["a", "b"] });
  });

  it("bulk upload sends a CSV as multipart", async () => {
    const { client, calls } = mockClient(() => envelope({ created_count: 1, errors: [], contacts: [], message: "ok" }));
    const result = await client.contacts.bulkUpload(new TextEncoder().encode("email\na@b.co\n"));
    expect(result.created_count).toBe(1);
    const form = calls[0]?.rawBody as FormData;
    expect(form).toBeInstanceOf(FormData);
    const file = form.get("file") as File;
    expect(file.name).toBe("contacts.csv");
    expect(file.type).toBe("text/csv");
  });

  it("activity returns an array; sample template returns csv text", async () => {
    const responses = [envelope([{ id: "1", title: "t" }]), envelope(null)];
    const { client } = mockClient(() => responses.shift()!);
    expect(await client.contacts.activity(ID)).toHaveLength(1);
    const csv = mockClient(() => new Response("email,first_name\n", { headers: { "Content-Type": "text/csv" } }));
    expect(await csv.client.contacts.sampleTemplate()).toBe("email,first_name\n");
  });
});

describe("templates", () => {
  it("CRUD, render, activate, archive", async () => {
    const { client, calls } = mockClient(() => envelope({ id: ID, subject: "Hi", html_content: "<b>Hi</b>" }));
    await client.templates.list({ status: "ACTIVE" });
    await client.templates.create({ name: "Welcome" });
    await client.templates.render(ID, { name: "Ada" });
    await client.templates.activate(ID);
    await client.templates.archive(ID);
    await client.templates.delete(ID);
    expect(query(calls[0]!.url)).toEqual({ status: "ACTIVE" });
    expect(calls[2]).toMatchObject({ method: "POST", body: { variables: { name: "Ada" } } });
    expect(calls[3]?.body).toEqual({ status: "ACTIVE" });
    expect(calls[4]?.body).toEqual({ status: "ARCHIVED" });
  });

  it("encodes path identifiers", async () => {
    const { client, calls } = mockClient(() => envelope({}));
    await client.templates.get("welcome slug/../x");
    expect(calls[0]?.url).toContain("/templates/welcome%20slug%2F..%2Fx/");
    await expect(client.templates.get("  ")).rejects.toBeInstanceOf(NovaValidationError);
  });

  it("surfaces 404s as NovaNotFoundError", async () => {
    const { client } = mockClient(() => errorEnvelope(404, "gone"));
    await expect(client.templates.get(ID)).rejects.toBeInstanceOf(NovaNotFoundError);
  });
});

describe("emails", () => {
  it("send validates input and never retries", async () => {
    const { client, calls } = mockClient(() => errorEnvelope(503, "down"), { maxRetries: 3 });
    await expect(client.emails.send({ recipient_email: "", subject: "s" })).rejects.toBeInstanceOf(NovaValidationError);
    await expect(client.emails.send({ recipient_email: "a@b.co", subject: "s" })).rejects.toThrow();
    expect(calls).toHaveLength(1);
  });

  it("send, bulkSend, groupSend, logs, preview", async () => {
    const { client, calls } = mockClient((call) => (call.url.includes("/logs/?") || call.url.endsWith("/logs/") ? envelope(page([])) : envelope({ id: ID, count: 2 })));
    await client.emails.send({ recipient_email: "a@b.co", subject: "Hi", html_content: "<p>x</p>" });
    await client.emails.bulkSend({ template_id: ID, contact_ids: [ID], sender_email: "me@x.co" });
    await client.emails.groupSend({ template_id: ID, group_id: ID, sender_email: "me@x.co" });
    await client.emails.listLogs({ status: "FAILED", page: 2 });
    await client.emails.getLog(ID);
    await client.emails.preview(ID);
    expect(calls.map((c) => `${c.method} ${path(c.url)}`)).toEqual([
      "POST /api/v1/emails/logs/send/",
      "POST /api/v1/emails/logs/bulk-send/",
      "POST /api/v1/emails/logs/group-send/",
      "GET /api/v1/emails/logs/",
      `GET /api/v1/emails/logs/${ID}/`,
      `GET /api/v1/emails/logs/${ID}/preview/`,
    ]);
    expect(query(calls[3]!.url)).toEqual({ status: "FAILED", page: "2" });
  });

  it("exports CSV as text or bytes", async () => {
    const { client, calls } = mockClient(() => new Response("a,b\n", { headers: { "Content-Type": "text/csv" } }));
    expect(await client.emails.exportCsv({ status: "DELIVERED" })).toBe("a,b\n");
    expect(Array.from(await client.emails.exportCsvBytes())).toEqual(Array.from(new TextEncoder().encode("a,b\n")));
    expect(query(calls[0]!.url)).toEqual({ status: "DELIVERED" });
  });
});

describe("providers, webhooks, campaigns", () => {
  it("providers", async () => {
    const { client, calls } = mockClient((call) => (call.url.includes("types") ? envelope([{ key: "SMTP" }]) : envelope({ id: ID })));
    expect(await client.providers.types()).toEqual([{ key: "SMTP" }]);
    await client.providers.create({ name: "Mailgun", provider_type: "MAILGUN" });
    await client.providers.update(ID, { is_active: false });
    await client.providers.test(ID, { recipient_email: "a@b.co" });
    await client.providers.delete(ID);
    await expect(client.providers.test(ID, { recipient_email: "" })).rejects.toBeInstanceOf(NovaValidationError);
    expect(calls.map((c) => c.method)).toEqual(["GET", "POST", "PATCH", "POST", "DELETE"]);
  });

  it("webhooks", async () => {
    const { client, calls } = mockClient((call) => (call.url.includes("events") ? envelope([{ key: "contact.created", label: "x" }]) : envelope({ id: ID, secret: "s" })));
    expect(await client.webhooks.events()).toHaveLength(1);
    await client.webhooks.create({ name: "n", url: "https://x.co/hook" });
    await client.webhooks.update(ID, { is_active: false });
    expect((await client.webhooks.rotateSecret(ID)).secret).toBe("s");
    expect(calls[3]?.rawBody).toBeUndefined();
    await client.webhooks.test(ID, { event_type: "contact.created" });
    await client.webhooks.delete(ID);
    expect(path(calls[4]!.url)).toBe(`/api/v1/webhooks/${ID}/send-test/`);
  });

  it("campaigns delegate to transactional notifications", async () => {
    const { client, calls } = mockClient(() => envelope({ id: ID, message_id: "MSG001" }));
    await client.campaigns.create({ name: "Welcome", api_identifier: "welcome" });
    await client.campaigns.sendTest(ID, { recipient_email: "a@b.co" });
    await client.campaigns.transactional.update(ID, { name: "W2" });
    await client.campaigns.delete(ID);
    expect(calls.map((c) => `${c.method} ${path(c.url)}`)).toEqual([
      "POST /api/v1/campaigns/transactional/",
      `POST /api/v1/campaigns/transactional/${ID}/send-test/`,
      `PATCH /api/v1/campaigns/transactional/${ID}/`,
      `DELETE /api/v1/campaigns/transactional/${ID}/`,
    ]);
    await expect(client.campaigns.sendTest(ID, { recipient_email: "" })).rejects.toBeInstanceOf(NovaValidationError);
  });
});

describe("analytics, audit, users", () => {
  it("analytics dashboard formats dates", async () => {
    const { client, calls } = mockClient(() => envelope({ total_contacts: 1 }));
    await client.analytics.dashboard({ date_from: "2026-01-01", date_to: new Date("2026-02-01T00:00:00Z") });
    expect(query(calls[0]!.url)).toEqual({ date_from: "2026-01-01", date_to: "2026-02-01T00:00:00.000Z" });
  });

  it("audit logs", async () => {
    const { client, calls } = mockClient((call) => (call.url.includes("stats") ? envelope({ total: 3 }) : call.url.endsWith(`${ID}/`) ? envelope({ id: ID }) : envelope(page([]))));
    await client.audit.accessLogs.list({ category: "AUTH", status_code_gte: 400, created_after: new Date("2026-01-01T00:00:00Z") });
    expect(query(calls[0]!.url)).toEqual({ category: "AUTH", status_code_gte: "400", created_after: "2026-01-01T00:00:00.000Z" });
    expect((await client.audit.stats()).total).toBe(3);
    await client.audit.get(ID);
    await client.audit.list();
  });

  it("users", async () => {
    const { client, calls } = mockClient((call) => (call.url.endsWith("/me/") ? envelope({ id: "u" }) : envelope(page([{ id: "u" }]))));
    expect((await client.users.list({ page_size: 5 })).items).toHaveLength(1);
    expect((await client.users.me()).id).toBe("u");
    expect(path(calls[1]!.url)).toBe("/api/v1/users/me/");
  });
});

describe("assets", () => {
  it("folders", async () => {
    const { client, calls } = mockClient(() => envelope({ id: ID, name: "Brand" }));
    await client.assets.folders.create({ name: " Brand " });
    await client.assets.folders.update(ID, { name: "B2" });
    await client.assets.folders.get(ID);
    await client.assets.folders.delete(ID);
    expect(calls[0]?.body).toEqual({ name: "Brand" });
    await expect(client.assets.folders.create({ name: "" })).rejects.toBeInstanceOf(NovaValidationError);
  });

  it("uploads bytes, Blobs and paths with inferred names and MIME types", async () => {
    const { client, calls } = mockClient(() => envelope({ id: ID }, { status: 201 }));
    await client.assets.files.upload(new Uint8Array([1]), { filename: "logo.png", folder: ID });
    const bytes = calls[0]?.rawBody as FormData;
    expect((bytes.get("file") as File).type).toBe("image/png");
    expect(bytes.get("folder")).toBe(ID);

    await client.assets.files.upload(new File(["x"], "doc.pdf", { type: "application/pdf" }));
    expect(((calls[1]?.rawBody as FormData).get("file") as File).name).toBe("doc.pdf");

    await client.assets.files.upload({ path: new URL("../package.json", import.meta.url).pathname });
    const fromPath = (calls[2]?.rawBody as FormData).get("file") as File;
    expect(fromPath.name).toBe("package.json");
    expect(fromPath.type).toBe("application/json");

    await client.assets.files.create(new Uint8Array([1]), { filename: "a.png", name: "Hero" });
    expect((calls[3]?.rawBody as FormData).get("name")).toBe("Hero");
  });

  it("rejects bad uploads before sending", async () => {
    const { client, calls } = mockClient(() => envelope({}));
    await expect(client.assets.files.upload(new Uint8Array([]), { filename: "a.png" })).rejects.toThrow(/empty/);
    await expect(client.assets.files.upload(new Uint8Array([1]))).rejects.toThrow(/filename/);
    await expect(client.assets.files.upload({ path: "/definitely/not/here.png" })).rejects.toThrow(/does not exist/);
    await expect(client.assets.files.upload("text" as never)).rejects.toBeInstanceOf(NovaValidationError);
    expect(calls).toHaveLength(0);
  });

  it("updates, lists and deletes files", async () => {
    const { client, calls } = mockClient((call) => (call.method === "GET" ? envelope(page([])) : envelope({ id: ID })));
    await client.assets.files.list({ folder_id: "root", search: "logo" });
    expect(query(calls[0]!.url)).toEqual({ folder_id: "root", search: "logo" });
    await client.assets.files.update(ID, { name: "renamed" });
    expect((calls[1]?.rawBody as URLSearchParams).get("name")).toBe("renamed");
    await client.assets.files.delete(ID);
    await expect(client.assets.files.update(ID, {})).rejects.toBeInstanceOf(NovaValidationError);
  });
});

describe("client", () => {
  it("withTenant returns an independent client", async () => {
    const other = "22222222-2222-2222-2222-222222222222";
    const { client, calls } = mockClient(() => envelope({}), { tenantId: TENANT });
    const scoped = client.withTenant(other);
    await scoped.templates.list();
    await client.templates.list();
    expect(calls.map((c) => c.headers["X-Tenant-ID"])).toEqual([other, TENANT]);
    expect(client.tenantId).toBe(TENANT);
  });

  it("per-call tenant overrides", async () => {
    const { client, calls } = mockClient(() => envelope({}));
    await client.templates.list({}, { tenantId: TENANT });
    expect(calls[0]?.headers["X-Tenant-ID"]).toBe(TENANT);
  });

  it("setters update the headers of later requests", async () => {
    const { client, calls } = mockClient(() => envelope({}));
    client.setTenantId(TENANT);
    client.setApiKey("nova_key_replaced");
    await client.health();
    expect(calls[0]?.headers).toMatchObject({ "X-Tenant-ID": TENANT, Authorization: "Bearer nova_key_replaced" });
    client.setTenantId(undefined);
    expect(client.tenantId).toBeUndefined();
  });

  it("is constructible without a tenant or credentials", () => {
    expect(() => new NovaClient({ baseUrl: "https://x.example" })).not.toThrow();
  });
});
