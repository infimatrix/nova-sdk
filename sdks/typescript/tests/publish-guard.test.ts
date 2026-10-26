import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const script = new URL("../scripts/require-artifact-registry.mjs", import.meta.url).pathname;

function run(env: Record<string, string>) {
  const empty = join(mkdtempSync(join(tmpdir(), "guard-")), "npmrc");
  writeFileSync(empty, "");
  const clean: Record<string, string> = { PATH: process.env["PATH"] ?? "", NPM_CONFIG_USERCONFIG: empty, NPM_CONFIG_GLOBALCONFIG: empty };
  return spawnSync(process.execPath, [script], { env: { ...clean, ...env }, encoding: "utf8" });
}

describe("publish guard", () => {
  it.each([
    ["default npm registry (nothing configured)", {}],
    ["public npm registry", { npm_config_registry: "https://registry.npmjs.org/" }],
    ["scoped public registry", { "npm_config_@infimatrix:registry": "https://registry.npmjs.org/" }],
    ["plain http Artifact Registry URL", { "npm_config_@infimatrix:registry": "http://us-central1-npm.pkg.dev/p/r/" }],
    ["look-alike host", { "npm_config_@infimatrix:registry": "https://us-central1-npm.pkg.dev.evil.example/p/r/" }],
    ["another company registry", { "npm_config_@infimatrix:registry": "https://npm.pkg.github.com/" }],
  ])("refuses %s", (_name, env) => {
    const result = run(env);
    expect(result.status).toBe(1);
    expect(result.stderr).toMatch(/Refusing to publish/);
  });

  it("accepts an Artifact Registry npm repository", () => {
    const result = run({ "npm_config_@infimatrix:registry": "https://europe-west1-npm.pkg.dev/some-project/some-repo/" });
    expect(result.status).toBe(0);
  });

  it("prefers the scoped registry over the default one", () => {
    const result = run({
      npm_config_registry: "https://registry.npmjs.org/",
      "npm_config_@infimatrix:registry": "https://us-central1-npm.pkg.dev/p/r/",
    });
    expect(result.status).toBe(0);
  });

  it("reads the scoped registry from an npmrc when run directly (as the release workflow does)", () => {
    const dir = mkdtempSync(join(tmpdir(), "guard-rc-"));
    const rc = join(dir, "npmrc");
    writeFileSync(rc, "@infimatrix:registry=https://us-central1-npm.pkg.dev/p/r/\n");
    expect(run({ NPM_CONFIG_USERCONFIG: rc }).status).toBe(0);
    writeFileSync(rc, "@infimatrix:registry=https://registry.npmjs.org/\n");
    expect(run({ NPM_CONFIG_USERCONFIG: rc }).status).toBe(1);
  });
});
