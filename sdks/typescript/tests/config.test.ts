import { inspect } from "node:util";
import { afterEach, describe, expect, it, vi } from "vitest";
import { NovaClient, NovaValidationError } from "../src/index.js";
import { buildHeaders, cleanCredential, redact, resolveConfig } from "../src/config.js";
import { TENANT } from "./helpers.js";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("resolveConfig", () => {
  it("applies defaults", () => {
    const config = resolveConfig({ apiKey: "k" });
    expect(config).toMatchObject({ baseUrl: "http://localhost:8000", timeoutMs: 30_000, maxRetries: 3 });
  });

  it("reads NOVA_* environment variables", () => {
    vi.stubEnv("NOVA_BASE_URL", "https://api.example.com/");
    vi.stubEnv("NOVA_API_KEY", "nova_key_env");
    vi.stubEnv("NOVA_TENANT_ID", TENANT.toUpperCase());
    const config = resolveConfig();
    expect(config.baseUrl).toBe("https://api.example.com");
    expect(config.apiKey).toBe("nova_key_env");
    expect(config.tenantId).toBe(TENANT);
  });

  it.each([
    ["https://api.example.com/api/v1", "https://api.example.com"],
    ["https://api.example.com/api/", "https://api.example.com"],
    ["https://api.example.com/proxy/nova///", "https://api.example.com/proxy/nova"],
  ])("normalises baseUrl %s", (input, expected) => {
    expect(resolveConfig({ baseUrl: input }).baseUrl).toBe(expected);
  });

  it.each([
    [{ baseUrl: "ftp://x" }],
    [{ baseUrl: "not a url" }],
    [{ timeoutMs: 0 }],
    [{ timeoutMs: Number.NaN }],
    [{ maxRetries: -1 }],
    [{ maxRetries: 1.5 }],
    [{ maxRetries: 11 }],
    [{ retryBackoffMs: -1 }],
    [{ tenantId: "not-a-uuid" }],
  ])("rejects invalid options %j", (options) => {
    expect(() => resolveConfig(options)).toThrow(NovaValidationError);
  });

  it("requires a fetch implementation", () => {
    vi.stubGlobal("fetch", undefined);
    expect(() => resolveConfig({})).toThrow(/fetch/);
  });
});

describe("credentials", () => {
  it("strips whitespace and Bearer prefixes", () => {
    expect(cleanCredential("  Bearer  Bearer abc ")).toBe("abc");
    expect(cleanCredential("bearer")).toBeUndefined();
    expect(cleanCredential("   ")).toBeUndefined();
    expect(cleanCredential(undefined)).toBeUndefined();
  });

  it("redacts for display", () => {
    expect(redact(undefined)).toBe("<none>");
    expect(redact("short")).toBe("[REDACTED]");
    expect(redact("nova_key_supersecretvalue")).toBe("nova_key...[REDACTED]");
  });

  it("prefers the API key over the access token", () => {
    const headers = buildHeaders(resolveConfig({ apiKey: "key", accessToken: "jwt", tenantId: TENANT }));
    expect(headers["Authorization"]).toBe("Bearer key");
    expect(headers["X-Tenant-ID"]).toBe(TENANT);
    expect(headers["User-Agent"]).toMatch(/^Nova-TypeScript-SDK\//);
  });

  it("falls back to the access token", () => {
    expect(buildHeaders(resolveConfig({ accessToken: "jwt" }))["Authorization"]).toBe("Bearer jwt");
  });

  it("never prints secrets", () => {
    const client = new NovaClient({ apiKey: "nova_key_supersecretvalue", accessToken: "jwt-supersecret-token" });
    for (const text of [
      JSON.stringify(client),
      JSON.stringify(client.config),
      inspect(client, { depth: 5 }),
      inspect(client.config, { depth: 5 }),
      String(client),
    ]) {
      expect(text).not.toContain("supersecret");
    }
    expect(String(client)).toContain("[REDACTED]");
  });
});

describe("browser guard", () => {
  it("refuses credentials in a browser unless explicitly allowed", () => {
    vi.stubGlobal("window", {});
    vi.stubGlobal("document", {});
    expect(() => new NovaClient({ apiKey: "nova_key_x" })).toThrow(/browser/i);
    expect(() => new NovaClient({ apiKey: "nova_key_x", dangerouslyAllowBrowser: true })).not.toThrow();
    expect(() => new NovaClient({})).not.toThrow();
  });
});
