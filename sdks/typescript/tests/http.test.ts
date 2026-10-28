import { createServer, type IncomingMessage, type Server } from "node:http";
import type { AddressInfo } from "node:net";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import {
  NovaAbortError,
  NovaAPIError,
  NovaAuthenticationError,
  NovaClient,
  NovaConnectionError,
  NovaNotFoundError,
  NovaPermissionError,
  NovaRateLimitError,
  NovaRedirectError,
  NovaServerError,
  NovaTimeoutError,
  NovaValidationError,
} from "../src/index.js";
import { sanitizeErrorText, sanitizeRedirectLocation } from "../src/http.js";
import { TENANT, envelope, errorEnvelope, mockClient } from "./helpers.js";

describe("URL building", () => {
  const { client } = mockClient(() => envelope({}));
  const build = (endpoint: string, params?: Record<string, never>) => client.http.buildUrl(endpoint, params);

  it("prefixes /api/v1 and adds a trailing slash", () => {
    expect(build("tenants")).toBe("http://localhost:8000/api/v1/tenants/");
    expect(build("/api/v1/tenants/")).toBe("http://localhost:8000/api/v1/tenants/");
    expect(build("api/v1")).toBe("http://localhost:8000/api/v1/");
  });

  it("keeps file extensions without a trailing slash", () => {
    expect(build("exports/logs.csv")).toBe("http://localhost:8000/api/v1/exports/logs.csv");
  });

  it("serialises query params, skipping empty values and repeating arrays", () => {
    const url = client.http.buildUrl("contacts/", { search: "a b", page: 2, skip: undefined, none: null, ids: [1, 2] });
    expect(url).toBe("http://localhost:8000/api/v1/contacts/?search=a+b&page=2&ids=1&ids=2");
  });
});

describe("request pipeline", () => {
  it("sends auth, tenant, correlation and user-agent headers", async () => {
    const { client, calls } = mockClient(() => envelope({ ok: true }), { tenantId: TENANT });
    await client.http.request("GET", "health/", { correlationId: " abc " });
    expect(calls[0]?.headers).toMatchObject({
      Authorization: "Bearer nova_key_test_secret_1234567890",
      "X-Tenant-ID": TENANT,
      "X-Correlation-ID": "abc",
      Accept: "application/json",
    });
  });

  it("allows per-call tenant overrides and validates them", async () => {
    const other = "22222222-2222-2222-2222-222222222222";
    const { client, calls } = mockClient(() => envelope({}), { tenantId: TENANT });
    await client.http.request("GET", "x/", { tenantId: other });
    expect(calls[0]?.headers["X-Tenant-ID"]).toBe(other);
    await expect(client.http.request("GET", "x/", { tenantId: "bad" })).rejects.toBeInstanceOf(NovaValidationError);
  });

  it("unwraps the envelope and keeps the correlation id", async () => {
    const { client } = mockClient(() => envelope({ a: 1 }));
    const res = await client.http.request("GET", "x/");
    expect(res).toMatchObject({ data: { a: 1 }, success: true, meta: { correlation_id: "corr-1" } });
  });

  it("handles 204, empty, csv, non-json and unenveloped bodies", async () => {
    const responses = [
      new Response(null, { status: 204 }),
      new Response("", { status: 200 }),
      new Response("a,b\n1,2\n", { status: 200, headers: { "Content-Type": "text/csv" } }),
      new Response("plain text", { status: 200 }),
      new Response(JSON.stringify([1, 2]), { status: 200 }),
    ];
    const { client } = mockClient(() => responses.shift()!);
    expect((await client.http.request("DELETE", "x/")).data).toBeNull();
    expect((await client.http.request("GET", "x/")).data).toBeNull();
    expect((await client.http.request("GET", "x/")).data).toBe("a,b\n1,2\n");
    expect((await client.http.request("GET", "x/")).data).toBe("plain text");
    expect((await client.http.request("GET", "x/")).data).toEqual([1, 2]);
  });

  it("sends JSON bodies with a content type", async () => {
    const { client, calls } = mockClient(() => envelope({}));
    await client.http.request("POST", "x/", { json: { a: 1 } });
    expect(calls[0]?.body).toEqual({ a: 1 });
    expect(calls[0]?.headers["Content-Type"]).toBe("application/json");
  });
});

describe("error mapping", () => {
  const cases: [number, new (...args: never[]) => Error][] = [
    [400, NovaValidationError],
    [401, NovaAuthenticationError],
    [403, NovaPermissionError],
    [404, NovaNotFoundError],
    [429, NovaRateLimitError],
    [500, NovaServerError],
    [418, NovaAPIError],
  ];

  it.each(cases)("maps HTTP %i", async (status, ErrorType) => {
    const { client } = mockClient(() => errorEnvelope(status, "boom", "CODE_X", { f: ["bad"] }), { maxRetries: 0 });
    const error = await client.http.request("POST", "x/").catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ErrorType);
    const nova = error as NovaAPIError;
    expect(nova.statusCode).toBe(status);
    expect(nova.errorCode).toBe("CODE_X");
    expect(nova.details).toEqual({ f: ["bad"] });
    expect(nova.correlationId).toBe("corr-err");
    expect(nova.message).toContain("boom");
    expect(nova.message).not.toContain("nova_key_test");
  });

  it("uses API_ERROR when no code is supplied", async () => {
    const { client } = mockClient(() => new Response("{}", { status: 404 }));
    const error = (await client.http.request("GET", "x/").catch((e: unknown) => e)) as NovaNotFoundError;
    expect(error.errorCode).toBe("API_ERROR");
  });

  it.each([
    ["legacy string error", { error: "Tenant context required." }, "Tenant context required."],
    ["detail only", { detail: "No tenant context." }, "No tenant context."],
    ["top-level message", { message: "Nope" }, "Nope"],
  ])("parses %s", async (_name, body, expected) => {
    const { client } = mockClient(() => new Response(JSON.stringify(body), { status: 400 }));
    const error = (await client.http.request("POST", "x/").catch((e: unknown) => e)) as NovaValidationError;
    expect(error.rawMessage).toBe(expected);
  });

  it("parses array bodies and DRF-style field errors", async () => {
    const arr = mockClient(() => new Response(JSON.stringify(["bad"]), { status: 400 }));
    const e1 = (await arr.client.http.request("POST", "x/").catch((e: unknown) => e)) as NovaValidationError;
    expect(e1.details).toEqual({ errors: ["bad"] });

    const drf = mockClient(() => new Response(JSON.stringify({ name: ["required"] }), { status: 400 }));
    const e2 = (await drf.client.http.request("POST", "x/").catch((e: unknown) => e)) as NovaValidationError;
    expect(e2.details).toEqual({ name: ["required"] });
  });

  it("summarises HTML and long text bodies", async () => {
    expect(sanitizeErrorText("<html><title> Bad Gateway </title></html>", 502)).toBe("HTTP 502 Error: Bad Gateway");
    expect(sanitizeErrorText("<html><body>x</body></html>", 502)).toBe("HTTP 502 Error (HTML response received)");
    expect(sanitizeErrorText("", 500)).toBe("HTTP 500 Error");
    expect(sanitizeErrorText("x".repeat(500), 500)).toHaveLength(200);
  });

  it("exposes Retry-After on rate limits", async () => {
    const { client } = mockClient(() => errorEnvelope(429, "slow", "RATE_LIMIT_EXCEEDED", {}, { "Retry-After": "7" }), {
      maxRetries: 0,
    });
    const error = (await client.http.request("GET", "x/").catch((e: unknown) => e)) as NovaRateLimitError;
    expect(error.retryAfter).toBe(7);
    expect(error.message).toContain("status=429");
  });
});

describe("retries", () => {
  it("retries idempotent requests on transient statuses", async () => {
    let n = 0;
    const { client, calls } = mockClient(() => (++n < 3 ? errorEnvelope(503, "down") : envelope({ ok: 1 })), { maxRetries: 3 });
    const res = await client.http.request("GET", "x/");
    expect(res.data).toEqual({ ok: 1 });
    expect(calls).toHaveLength(3);
  });

  it("stops after maxRetries and raises the last error", async () => {
    const { client, calls } = mockClient(() => errorEnvelope(503, "down"), { maxRetries: 2 });
    await expect(client.http.request("GET", "x/")).rejects.toBeInstanceOf(NovaServerError);
    expect(calls).toHaveLength(3);
  });

  it.each(["POST", "PUT", "PATCH", "DELETE"])("never retries %s by default", async (method) => {
    const { client, calls } = mockClient(() => errorEnvelope(503, "down"), { maxRetries: 3 });
    await expect(client.http.request(method, "x/")).rejects.toBeInstanceOf(NovaServerError);
    expect(calls).toHaveLength(1);
  });

  it("retries a non-idempotent request when explicitly allowed", async () => {
    let n = 0;
    const { client, calls } = mockClient(() => (++n < 2 ? errorEnvelope(502, "bad") : envelope({})), { maxRetries: 2 });
    await client.http.request("POST", "x/", { allowRetry: true });
    expect(calls).toHaveLength(2);
  });

  it("does not retry non-transient statuses", async () => {
    const { client, calls } = mockClient(() => errorEnvelope(404, "nope"), { maxRetries: 3 });
    await expect(client.http.request("GET", "x/")).rejects.toBeInstanceOf(NovaNotFoundError);
    expect(calls).toHaveLength(1);
  });

  it("honours Retry-After (capped at 30s) instead of the backoff", async () => {
    let n = 0;
    const started = Date.now();
    const { client } = mockClient(
      () => (++n < 2 ? errorEnvelope(429, "slow", "RATE_LIMIT_EXCEEDED", {}, { "Retry-After": "0.05" }) : envelope({})),
      { maxRetries: 1, retryBackoffMs: 5000 },
    );
    await client.http.request("GET", "x/");
    expect(Date.now() - started).toBeLessThan(2000);
  });

  it("retries network failures for idempotent requests only", async () => {
    let n = 0;
    const flaky = mockClient(
      () => {
        if (++n < 2) throw new TypeError("fetch failed");
        return envelope({ ok: 1 });
      },
      { maxRetries: 2 },
    );
    expect((await flaky.client.http.request("GET", "x/")).data).toEqual({ ok: 1 });

    const post = mockClient(
      () => {
        throw new TypeError("fetch failed");
      },
      { maxRetries: 2 },
    );
    await expect(post.client.http.request("POST", "x/")).rejects.toBeInstanceOf(NovaConnectionError);
    expect(post.calls).toHaveLength(1);
  });
});

describe("redirects", () => {
  it("raises NovaRedirectError and strips embedded credentials from the location", async () => {
    const { client } = mockClient(
      () => new Response(null, { status: 302, headers: { Location: "https://user:pw@evil.example/x" } }),
    );
    const error = (await client.http.request("GET", "x/").catch((e: unknown) => e)) as NovaRedirectError;
    expect(error).toBeInstanceOf(NovaRedirectError);
    expect(error.location).toBe("https://evil.example/x");
    expect(error.message).not.toContain("pw");
    expect(sanitizeRedirectLocation(null)).toBeUndefined();
  });
});

describe("real network behaviour (local server)", () => {
  let server: Server;
  let base: string;
  let lastRequest: { headers: IncomingMessage["headers"]; body: string } | undefined;
  let redirectedHits = 0;

  beforeAll(async () => {
    server = createServer((req, res) => {
      const chunks: Buffer[] = [];
      req.on("data", (c: Buffer) => chunks.push(c));
      req.on("end", () => {
        lastRequest = { headers: req.headers, body: Buffer.concat(chunks).toString() };
        if (req.url?.startsWith("/api/v1/slow/")) return; // never answer: exercises timeouts
        if (req.url?.startsWith("/api/v1/redirect/")) {
          res.writeHead(302, { Location: "/api/v1/redirected/" });
          return res.end();
        }
        if (req.url?.startsWith("/api/v1/redirected/")) {
          redirectedHits++;
          res.writeHead(200, { "Content-Type": "application/json" });
          return res.end("{}");
        }
        res.writeHead(200, { "Content-Type": "application/json", "X-Correlation-ID": "srv-1" });
        res.end(JSON.stringify({ success: true, message: "ok", data: { echoed: true }, errors: null, meta: {} }));
      });
    });
    await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
    base = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  });

  afterAll(() => new Promise<void>((resolve) => server.close(() => resolve())));

  it("talks to a real HTTP server with the global fetch", async () => {
    const client = new NovaClient({ baseUrl: `${base}/api/v1`, apiKey: "nova_key_real", tenantId: TENANT });
    const res = await client.http.request("GET", "echo/");
    expect(res.data).toEqual({ echoed: true });
    expect(res.meta.correlation_id).toBe("srv-1");
    expect(lastRequest?.headers["authorization"]).toBe("Bearer nova_key_real");
    expect(lastRequest?.headers["x-tenant-id"]).toBe(TENANT);
  });

  it("does not follow redirects", async () => {
    const client = new NovaClient({ baseUrl: base, apiKey: "nova_key_real", maxRetries: 0 });
    await expect(client.http.request("GET", "redirect/")).rejects.toBeInstanceOf(NovaRedirectError);
    expect(redirectedHits).toBe(0);
  });

  it("times out", async () => {
    const client = new NovaClient({ baseUrl: base, apiKey: "nova_key_real", timeoutMs: 100, maxRetries: 0 });
    await expect(client.http.request("GET", "slow/")).rejects.toBeInstanceOf(NovaTimeoutError);
  });

  it("aborts via AbortSignal", async () => {
    const client = new NovaClient({ baseUrl: base, apiKey: "nova_key_real", maxRetries: 0 });
    const controller = new AbortController();
    const pending = client.http.request("GET", "slow/", { signal: controller.signal });
    setTimeout(() => controller.abort(), 50);
    await expect(pending).rejects.toBeInstanceOf(NovaAbortError);
  });

  it("fails with a connection error when nothing listens", async () => {
    const client = new NovaClient({ baseUrl: "http://127.0.0.1:1", apiKey: "nova_key_real", maxRetries: 0 });
    await expect(client.http.request("GET", "x/")).rejects.toBeInstanceOf(NovaConnectionError);
  });

  it("uploads multipart bodies", async () => {
    const client = new NovaClient({ baseUrl: base, apiKey: "nova_key_real" });
    await client.assets.files.upload(new Uint8Array([1, 2, 3]), { filename: "a.png", folder: "f1" });
    expect(String(lastRequest?.headers["content-type"])).toMatch(/^multipart\/form-data; boundary=/);
    expect(lastRequest?.body).toContain('filename="a.png"');
    expect(lastRequest?.body).toContain('name="folder"');
  });
});

describe("conformance regressions", () => {
  it.each([".", ".."])("rejects the dot-segment path id %s before any request", async (id) => {
    const { client, calls } = mockClient(() => envelope({ id: "x" }));
    await expect(client.templates.get(id)).rejects.toBeInstanceOf(NovaValidationError);
    await expect(client.templates.delete(id)).rejects.toBeInstanceOf(NovaValidationError);
    expect(calls).toHaveLength(0);
  });

  it("sends a literal %2e%2e id encoded, so it round-trips as data", async () => {
    const { client, calls } = mockClient(() => envelope({ id: "x" }));
    await client.templates.get("%2e%2e");
    expect(new URL(calls[0]!.url).pathname).toBe("/api/v1/templates/%252e%252e/");
  });

  it("treats a JSON-declared response with an invalid body as an error, not success", async () => {
    const { client } = mockClient(
      () => new Response("{not json", { status: 200, headers: { "Content-Type": "application/json", "X-Correlation-ID": "c-1" } }),
    );
    const err = await client.templates.get("t-1").catch((e: unknown) => e);
    expect(err).toBeInstanceOf(NovaAPIError);
    expect(err).toMatchObject({ statusCode: 200, errorCode: "INVALID_RESPONSE", correlationId: "c-1" });
  });

  it("still returns non-JSON content types as text", async () => {
    const { client } = mockClient(() => new Response("plain text", { status: 200, headers: { "Content-Type": "text/plain" } }));
    expect((await client.http.request("GET", "files/x.txt")).data).toBe("plain text");
  });
});

describe("redirect location credential stripping", () => {
  it.each([
    ["http://user:pw@host.example/p?q=1#f", "http://host.example/p?q=1#f"],
    ["http://user:se@cret@host.example/next", "http://host.example/next"], // '@' inside the password
    ["http://u:p%40ss@host.example:8443/x", "http://host.example:8443/x"],
    ["http://:onlypw@host.example/", "http://host.example/"],
    ["http://host.example/a@b", "http://host.example/a@b"], // '@' in the path is not userinfo
  ])("%s -> %s", (location, expected) => {
    expect(sanitizeRedirectLocation(location)).toBe(expected);
  });
});
