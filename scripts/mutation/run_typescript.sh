#!/usr/bin/env bash
# StrykerJS on the handwritten TypeScript transport. Needs Node >= 22. Usage: scripts/mutation/run_typescript.sh [workdir]
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
work="${1:-$(mktemp -d)}"
mkdir -p "$work"
rm -rf "$work/ts" && mkdir -p "$work/ts"
cd "$root/sdks/typescript" && cp -r package.json package-lock.json tsconfig.json tsup.config.ts vitest.config.ts src tests "$work/ts/"
cd "$work/ts"
npm ci --silent
npm install --no-save --silent @stryker-mutator/core@10.1.1 @stryker-mutator/vitest-runner@10.1.1
cat > stryker.config.json <<'EOF'
{
  "testRunner": "vitest",
  "mutate": ["src/http.ts", "src/config.ts", "src/errors.ts", "src/models.ts"],
  "reporters": ["clear-text", "json"],
  "jsonReporter": { "fileName": "reports/mutation.json" },
  "concurrency": 3,
  "timeoutMS": 20000,
  "coverageAnalysis": "perTest"
}
EOF
npx stryker run
echo "report: $work/ts/reports/mutation.json"
