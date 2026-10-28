/**
 * Retry delays and request-level overrides, pinned from docs/conventions.md and docs/error-handling.md.
 * Found by mutation testing (Stryker): retry counts were tested, but not how long the client waits, whether
 * Retry-After is honoured and capped, or whether per-request headers / retry overrides are applied.
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import { NovaRedirectError, NovaServerError } from "../src/index.js";
import { envelope, errorEnvelope, mockClient } from "./helpers.js";

const TIMEOUT_MS = 12_345; // distinguishes the request timeout timer from retry waits

/** Record retry waits and run them immediately; leave the request-timeout timer real. */
function captureWaits(): number[] {
  const waits: number[] = [];
  const real = globalThis.setTimeout;
  vi.spyOn(globalThis, "setTimeout").mockImplementation(((fn: () => void, ms?: number) => {
    if (ms === TIMEOUT_MS) return real(fn, ms);
    waits.push(ms ?? 0);
    fn();
    return 0 as unknown as ReturnType<typeof setTimeout>;
  }) as typeof setTimeout);
  return waits;
}

afterEach(() => vi.restoreAllMocks());

describe("retry delays", () => {
  it("backoff doubles each attempt without jitter (base * 2^attempt)", async () => {
    const waits = captureWaits();
    const { client } = mockClient(() => errorEnvelope(503, "x"), { maxRetries: 3, retryBackoffMs: 1000, retryJitter: false, timeoutMs: TIMEOUT_MS });
    await expect(client.health()).rejects.toBeInstanceOf(NovaServerError);
    expect(waits).toEqual([1000, 2000, 4000]);
  });

  it("jittered backoff stays between half and the full delay", async () => {
    const waits = captureWaits();
    const { client } = mockClient(() => errorEnvelope(503, "x"), { maxRetries: 3, retryBackoffMs: 1000, retryJitter: true, timeoutMs: TIMEOUT_MS });
    await expect(client.health()).rejects.toBeInstanceOf(NovaServerError);
    expect(waits).toHaveLength(3);
    waits.forEach((w, attempt) => {
      expect(w).toBeGreaterThanOrEqual(500 * 2 ** attempt);
      expect(w).toBeLessThanOrEqual(1000 * 2 ** attempt);
    });
  });

  it.each([
    ["7", 7000],
    ["0", 0], // RFC 9110: zero seconds means retry immediately
    ["2.5", 2500],
    ["120", 30_000], // docs: capped at 30 s
  ])("Retry-After %s -> wait %i ms", async (header, expectedMs) => {
    const waits = captureWaits();
    let calls = 0;
    const { client } = mockClient(
      () => (calls++ === 0 ? errorEnvelope(429, "slow", "RATE_LIMIT_EXCEEDED", {}, { "Retry-After": header }) : envelope({ ok: true })),
      { maxRetries: 2, retryBackoffMs: 3000, retryJitter: false, timeoutMs: TIMEOUT_MS },
    );
    await client.health();
    expect(waits).toEqual([expectedMs]);
  });

  it.each(["soon", "Wed, 21 Oct 2026 07:28:00 GMT"])("unusable Retry-After %j falls back to backoff", async (header) => {
    const waits = captureWaits();
    let calls = 0;
    const { client } = mockClient(
      () => (calls++ === 0 ? errorEnvelope(503, "x", "API_ERROR", {}, { "Retry-After": header }) : envelope({})),
      { maxRetries: 1, retryBackoffMs: 3000, retryJitter: false, timeoutMs: TIMEOUT_MS },
    );
    await client.health();
    expect(waits).toEqual([3000]);
  });

  it("allowRetry overrides the method default in both directions", async () => {
    captureWaits();
    let posts = 0;
    const a = mockClient(() => (posts++, errorEnvelope(503, "x")), { maxRetries: 2, retryJitter: false, timeoutMs: TIMEOUT_MS });
    await expect(a.client.http.request("POST", "emails/logs/send/", { json: {}, allowRetry: true })).rejects.toBeInstanceOf(NovaServerError);
    expect(posts).toBe(3);
    let gets = 0;
    const b = mockClient(() => (gets++, errorEnvelope(503, "x")), { maxRetries: 2, retryJitter: false, timeoutMs: TIMEOUT_MS });
    await expect(b.client.http.request("GET", "health/", { allowRetry: false })).rejects.toBeInstanceOf(NovaServerError);
    expect(gets).toBe(1);
  });
});

describe("request-level overrides and status boundaries", () => {
  it("sends per-request headers and the correlation id without displacing auth", async () => {
    const { client, calls } = mockClient(() => envelope({}), { apiKey: "nova_key_abc" });
    await client.health({ headers: { "X-Custom": "v1" }, correlationId: "corr-77" });
    const h = Object.fromEntries(Object.entries(calls[0]!.headers).map(([k, v]) => [k.toLowerCase(), v]));
    expect(h["x-custom"]).toBe("v1");
    expect(h["x-correlation-id"]).toBe("corr-77");
    expect(h["authorization"]).toBe("Bearer nova_key_abc");
  });

  it.each([300, 301, 303, 304, 399])("HTTP %i is an unexpected redirect", async (status) => {
    const { client } = mockClient(() => new Response(null, { status, headers: { Location: "/elsewhere/" } }));
    const err = await client.health().catch((e: unknown) => e);
    expect(err).toBeInstanceOf(NovaRedirectError);
    expect(err).toMatchObject({ statusCode: status });
  });

  it.each([200, 201, 202, 203, 299])("HTTP %i is success", async (status) => {
    const { client } = mockClient(() => envelope({ n: status }, { status }));
    expect(await client.health()).toEqual({ n: status });
  });
});
