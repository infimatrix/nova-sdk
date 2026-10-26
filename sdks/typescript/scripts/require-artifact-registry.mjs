#!/usr/bin/env node
// Safeguard: this package is distributed only through Google Cloud Artifact Registry.
// Refuse to publish when the effective registry for the @infimatrix scope is anything else
// (in particular the public npm registry, which is npm's default).
import { spawnSync } from "node:child_process";

const scope = "@infimatrix";

// Inside an npm lifecycle script the effective settings are exported as env vars; when the
// guard is run directly (as the release workflow does) ask npm for them.
function npmConfig(key) {
  const result = spawnSync("npm", ["config", "get", key], { encoding: "utf8" });
  const value = result.status === 0 ? result.stdout.trim() : "";
  return value && value !== "undefined" && value !== "null" ? value : undefined;
}

const registry =
  process.env[`npm_config_${scope}:registry`] ??
  process.env.npm_config_registry ??
  npmConfig(`${scope}:registry`) ??
  npmConfig("registry") ??
  "https://registry.npmjs.org/";

let host = "";
try {
  const url = new URL(registry);
  host = url.protocol === "https:" ? url.hostname : "";
} catch {
  /* fall through */
}

if (!/^[a-z0-9-]+-npm\.pkg\.dev$/.test(host)) {
  console.error(
    `Refusing to publish: registry "${registry}" is not a Google Cloud Artifact Registry npm repository.\n` +
      `Set ${scope}:registry to https://<LOCATION>-npm.pkg.dev/<PROJECT>/<REPOSITORY>/ (see docs/releasing.md).`,
  );
  process.exit(1);
}
console.log(`Publish target OK: ${host}`);
