/**
 * Property tests for invariants the documentation states (docs/conventions.md, authentication.md).
 * Each property cites its source and asserts nothing the docs do not promise. A failing run prints the seed and path;
 * replay with `fc.assert(..., { seed, path })`.
 */
import fc from "fast-check";
import { describe, expect, it } from "vitest";
import { NovaClient, NovaError, NovaValidationError } from "../src/index.js";
import { envelope, errorEnvelope, mockClient, page } from "./helpers.js";

const RUNS = { numRuns: 200 };
const PREFIX = "/api/v1/templates/";

describe("properties", () => {
  it("a path id never adds segments or a query string (conventions: Path ids)", async () => {
    await fc.assert(
      fc.asyncProperty(fc.string({ maxLength: 40 }), async (identifier) => {
        const { client, calls } = mockClient(() => envelope({ id: "x", name: "n" }));
        const stripped = identifier.trim();
        if (!stripped || stripped === "." || stripped === "..") {
          await expect(client.templates.get(identifier)).rejects.toBeInstanceOf(NovaValidationError);
          expect(calls).toHaveLength(0);
          return;
        }
        await client.templates.get(identifier);
        expect(calls).toHaveLength(1);
        const url = new URL(calls[0]!.url);
        expect(url.search).toBe("");
        expect(url.hash).toBe("");
        const raw = url.pathname;
        expect(raw.startsWith(PREFIX) && raw.endsWith("/")).toBe(true);
        const segment = raw.slice(PREFIX.length, -1);
        expect(segment.includes("/")).toBe(false);
        expect(segment === "." || segment === "..").toBe(false);
        expect(decodeURIComponent(segment)).toBe(stripped);
      }),
      RUNS,
    );
  });

  it("a search value reaches the server unchanged (RFC 3986)", async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 40 }).filter((s) => s.trim() === s && s !== ""),
        async (value) => {
          const { client, calls } = mockClient(() => envelope(page([])));
          await client.templates.list({ search: value });
          const sent = new URL(calls[0]!.url).searchParams.getAll("search");
          expect(sent).toEqual([value]);
        },
      ),
      RUNS,
    );
  });

  it("base URL normalisation strips '/', '/api', '/api/v1' and is stable (conventions: Base URL)", () => {
    fc.assert(
      fc.property(
        fc.stringMatching(/^[a-z][a-z0-9]{0,10}(\.[a-z]{2,6}){0,2}$/),
        fc.constantFrom("", "/", "/api", "/api/", "/api/v1", "/api/v1/"),
        fc.option(fc.integer({ min: 1, max: 65535 }), { nil: undefined }),
        (host, suffix, port) => {
          const origin = `http://${host}${port ? `:${port}` : ""}`;
          const once = new NovaClient({ baseUrl: origin + suffix, apiKey: "k" }).config.baseUrl;
          expect(once).toBe(origin);
          expect(new NovaClient({ baseUrl: once, apiKey: "k" }).config.baseUrl).toBe(once);
        },
      ),
      RUNS,
    );
  });

  it("the API key never appears in errors or their string forms (authentication: Handling secrets)", async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.stringMatching(/^[A-Za-z0-9]{8,40}$/),
        fc.constantFrom(400, 401, 403, 404, 409, 418, 429, 500, 502, 503),
        async (key, status) => {
          const secret = `nova_key_${key}`;
          const { client } = mockClient(() => errorEnvelope(status, "failure"), { apiKey: secret, maxRetries: 0 });
          const err = await client.templates.create({ name: "n" }).catch((e: unknown) => e);
          expect(err).toBeInstanceOf(NovaError);
          const forms = [String(err), JSON.stringify(err), (err as Error).message, String(client), JSON.stringify(client)];
          for (const text of forms) expect(text.includes(secret)).toBe(false);
        },
      ),
      RUNS,
    );
  });

  it("iteration visits every item once, in order (conventions: Pagination)", async () => {
    await fc.assert(
      fc.asyncProperty(fc.array(fc.integer({ min: 0, max: 5 }), { minLength: 1, maxLength: 6 }), async (sizes) => {
        let n = 0;
        const pages = sizes.map((size) => Array.from({ length: size }, () => ({ id: `id-${n++}`, name: "n" })));
        const requested: number[] = [];
        const { client } = mockClient((call) => {
          const p = Number(new URL(call.url).searchParams.get("page") ?? "1");
          requested.push(p);
          return envelope(page(pages[p - 1]!, p, pages.length, n));
        });
        const ids: string[] = [];
        for await (const t of await client.templates.list({ page_size: 10 })) ids.push(t.id);
        expect(ids).toEqual(pages.flat().map((t) => t.id));
        expect(requested).toEqual(pages.map((_, i) => i + 1));
      }),
      RUNS,
    );
  });
});
