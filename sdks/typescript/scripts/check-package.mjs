#!/usr/bin/env node
// Verifies the published artifact, not the source tree: packs the package, installs the
// tarball into a scratch project, and exercises ESM, CJS and TypeScript consumers.
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const pkg = JSON.parse(readFileSync(join(root, "package.json"), "utf8"));
const scratch = mkdtempSync(join(tmpdir(), "nova-sdk-pack-"));
const run = (cmd, args, cwd = root) => execFileSync(cmd, args, { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "inherit"] });
const fail = (message) => {
  console.error(`check-package: ${message}`);
  process.exitCode = 1;
};

try {
  const [packed] = JSON.parse(run("npm", ["pack", "--json", "--pack-destination", scratch]));
  const files = new Set(packed.files.map((f) => f.path));
  for (const required of [
    "package.json",
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "dist/index.js",
    "dist/index.cjs",
    "dist/index.d.ts",
    "dist/index.d.cts",
  ]) {
    if (!files.has(required)) fail(`tarball is missing ${required}`);
  }
  for (const path of files) {
    if (/^(src|tests|scripts|node_modules)\//.test(path) || path.endsWith(".env")) fail(`tarball must not contain ${path}`);
  }

  const consumer = join(scratch, "consumer");
  run("mkdir", ["-p", consumer]);
  writeFileSync(join(consumer, "package.json"), JSON.stringify({ name: "consumer", private: true, type: "module" }));
  run("npm", ["install", "--no-audit", "--no-fund", join(scratch, packed.filename)], consumer);

  const esm = run("node", ["--input-type=module", "-e", `import { NovaClient, VERSION } from "${pkg.name}"; const c = new NovaClient({ apiKey: "k" }); console.log(VERSION, typeof c.contacts.list);`], consumer).trim();
  if (esm !== `${pkg.version} function`) fail(`ESM smoke test printed "${esm}"`);

  const cjs = run("node", ["-e", `const { NovaClient, VERSION } = require("${pkg.name}"); const c = new NovaClient({ apiKey: "k" }); console.log(VERSION, typeof c.contacts.list);`], consumer).trim();
  if (cjs !== `${pkg.version} function`) fail(`CJS smoke test printed "${cjs}"`);

  // Type-level check from both module systems.
  writeFileSync(
    join(consumer, "tsconfig.json"),
    JSON.stringify({ compilerOptions: { module: "NodeNext", moduleResolution: "NodeNext", strict: true, noEmit: true, skipLibCheck: false, types: [] }, files: ["use.mts", "use.cts"] }),
  );
  const usage = `import { NovaClient, Page, NovaNotFoundError, type Tenant } from "${pkg.name}";
const nova = new NovaClient({ apiKey: "k" });
export async function demo(): Promise<string | undefined> {
  const page: Page<Tenant> = await nova.tenants.list();
  try { await nova.templates.get("x"); } catch (e) { if (e instanceof NovaNotFoundError) return e.correlationId; }
  return page.items[0]?.name;
}
`;
  writeFileSync(join(consumer, "use.mts"), usage);
  writeFileSync(join(consumer, "use.cts"), usage.replace(/^import (.*) from/m, "import $1 from"));
  run(join(root, "node_modules", ".bin", "tsc"), ["-p", "tsconfig.json"], consumer);

  if (!process.exitCode) console.log(`check-package: ${packed.filename} OK (${files.size} files, ESM + CJS + types)`);
} finally {
  rmSync(scratch, { recursive: true, force: true });
}
