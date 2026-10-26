import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import * as sdk from "../src/index.js";

const pkg = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8")) as {
  name: string;
  version: string;
  type: string;
  engines: { node: string };
  dependencies?: Record<string, string>;
  exports: Record<string, unknown>;
};

describe("package metadata", () => {
  it("keeps VERSION in sync with package.json", () => {
    expect(sdk.VERSION).toBe(pkg.version);
  });

  it("has no runtime dependencies", () => {
    expect(pkg.dependencies ?? {}).toEqual({});
  });

  it("declares ESM + CJS entry points and a Node floor with global fetch", () => {
    expect(pkg.type).toBe("module");
    expect(pkg.exports["."]).toMatchObject({ import: { types: expect.any(String) }, require: { types: expect.any(String) } });
    expect(pkg.engines.node).toMatch(/>=18/);
  });

  it("exports the public API", () => {
    for (const name of ["NovaClient", "Page", "NovaError", "NovaRateLimitError", "HttpTransport", "VERSION"]) {
      expect(sdk).toHaveProperty(name);
    }
  });

  it("does not import Node-only modules at load time", () => {
    const sources = ["files.ts", "http.ts", "config.ts", "client.ts"].map((f) => readFileSync(new URL(`../src/${f}`, import.meta.url), "utf8"));
    for (const source of sources) expect(source).not.toMatch(/^import .* from "node:/m);
  });
});
