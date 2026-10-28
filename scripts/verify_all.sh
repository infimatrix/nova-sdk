#!/usr/bin/env bash
# Verify the whole repository from a CLEAN COPY of the working tree, using isolated environments.
#
#   scripts/verify_all.sh [workdir]
#
# Needs: python3 (3.10+), node 20+ with npm, JDK 17+, Maven 3.9+, curl (for the pinned gitleaks download).
# Optional: actionlint on PATH. Nothing is published or uploaded: builds stay in <workdir>, Maven installs only into
# <workdir>/m2, npm/pip only into <workdir>.
#
# Every check prints PASS or FAIL from the command's real exit status; logs are kept in <workdir>/logs.
# Exit status is non-zero if any check failed. A check that cannot run reports NOT RUN with the reason.
set -u
root="$(cd "$(dirname "$0")/.." && pwd)"
work="${1:-$(mktemp -d)}"
mkdir -p "$work/logs"
fail=0
declare -a summary

run() { # run <name> <dir> <command...>
  local name="$1" dir="$2"; shift 2
  local log="$work/logs/${name//[^A-Za-z0-9._-]/_}.log"
  ( cd "$dir" && "$@" ) >"$log" 2>&1
  local rc=$?
  if [ $rc -eq 0 ]; then summary+=("PASS     $name"); else summary+=("FAIL     $name (exit $rc, see $log)"); fail=1; fi
}
skip() { summary+=("NOT RUN  $1 ($2)"); }

# ---------------------------------------------------------------- clean copy of the tracked + new (non-ignored) files
src="$work/src"
rm -rf "$src" && mkdir -p "$src"
( cd "$root" && git ls-files -z --cached --others --exclude-standard | xargs -0 -I{} cp --parents {} "$src" )
echo "clean copy: $src ($(find "$src" -type f | wc -l) files)"

py="$work/venv/bin/python"
python3 -m venv "$work/venv"
run "python: install dev deps" "$src" "$work/venv/bin/pip" install -q -r requirements-dev.txt -e "sdks/python[dev]" hypothesis build twine pip-audit bandit

# ---------------------------------------------------------------- contract and generators
run "contract+checker tests (pytest tests)"        "$src" "$py" -m pytest -q tests
for g in gen_python_models gen_python_async gen_ts_types gen_java_models; do
  run "generated code up to date: $g" "$src" "$py" "scripts/$g.py" --check
done
run "SDK coverage of the contract (strict)"        "$src" "$py" scripts/check_sdk_coverage.py --strict
if command -v actionlint >/dev/null; then run "actionlint" "$src" actionlint; else skip "actionlint" "not installed"; fi
run "workflow YAML parses"                         "$src" "$py" -c "import glob,yaml;[yaml.safe_load(open(f)) for f in glob.glob('.github/**/*.yml',recursive=True)]"

# ---------------------------------------------------------------- Python SDK
py_sdk="$src/sdks/python"
run "python: ruff check"                           "$py_sdk" "$work/venv/bin/ruff" check .
run "python: ruff format --check"                  "$py_sdk" "$work/venv/bin/ruff" format --check .
run "python: mypy"                                 "$py_sdk" "$work/venv/bin/mypy"
run "python: pytest (unit + property)"             "$py_sdk" "$py" -m pytest -q -p no:cacheprovider
run "python: build sdist+wheel"                    "$py_sdk" "$py" -m build --outdir "$work/py-dist"
run "python: twine check"                          "$py_sdk" "$work/venv/bin/twine" check "$work/py-dist"/*
python3 -m venv "$work/py-clean"
run "python: wheel installs in a clean venv"       "$work" "$work/py-clean/bin/pip" install -q "$work"/py-dist/*.whl
run "python: import smoke test (outside source)"   "$work" "$work/py-clean/bin/python" -I -c "import nova_sdk, nova_sdk.aio; from nova_sdk import NovaClient; NovaClient(api_key='k'); print(nova_sdk.__version__)"
python3 -m venv "$work/py-clean-sdist"
run "python: sdist installs in a clean venv"       "$work" "$work/py-clean-sdist/bin/pip" install -q "$work"/py-dist/*.tar.gz
run "python: pip-audit (runtime dependencies)"     "$work" sh -c "'$work/venv/bin/pip-audit' --path \"\$(echo '$work'/py-clean/lib/python3*/site-packages)\""
run "python: bandit (medium+)"                     "$src" "$work/venv/bin/bandit" -q -r sdks/python/src scripts tests/conformance/conformance.py -ll

# ---------------------------------------------------------------- TypeScript SDK
ts="$src/sdks/typescript"
run "typescript: npm ci"                           "$ts" npm ci --no-audit --no-fund
run "typescript: typecheck"                        "$ts" npm run typecheck
run "typescript: tests (unit + property)"          "$ts" npm test
run "typescript: build"                            "$ts" npm run build
run "typescript: check:package"                    "$ts" npm run check:package
run "typescript: npm audit (production)"           "$ts" npm audit --omit=dev --audit-level=low
run "typescript: npm audit (dev tooling, high)"    "$ts" npm audit --audit-level=high
mkdir -p "$work/ts-pack" && run "typescript: npm pack" "$ts" npm pack --pack-destination "$work/ts-pack"
consumer="$work/ts-consumer"; mkdir -p "$consumer"
run "typescript: tarball installs in a clean project" "$consumer" sh -c "npm init -y >/dev/null && npm install --no-audit --no-fund '$work'/ts-pack/*.tgz"
run "typescript: ESM import smoke test"            "$consumer" node --input-type=module -e "import {NovaClient,VERSION} from '@infimatrix/nova-sdk'; new NovaClient({apiKey:'k'}); console.log(VERSION)"
run "typescript: CJS require smoke test"           "$consumer" node -e "const {NovaClient,VERSION}=require('@infimatrix/nova-sdk'); new NovaClient({apiKey:'k'}); console.log(VERSION)"

# ---------------------------------------------------------------- Java SDK
jv="$src/sdks/java"
run "java: mvn clean verify"                       "$jv" mvn -B -ntp clean verify
run "java: install into a throw-away local repo"   "$jv" mvn -B -ntp -DskipTests "-Dmaven.repo.local=$work/m2" install
run "java: consumer smoke test (separate project)" "$src" sdks/java/scripts/smoke-test.sh "$work/m2"

# ---------------------------------------------------------------- cross-language
run "conformance: python+typescript+java"          "$src" "$py" tests/conformance/conformance.py --json-out "$work/conformance.json"

# ---------------------------------------------------------------- build reproducibility (same inputs -> same bytes)
rebuild_py() { cp -r "$src/sdks/python" "$work/py-rebuild" && ( cd "$work/py-rebuild" && SOURCE_DATE_EPOCH=1767225600 "$py" -m build --outdir "$work/py-dist2" >/dev/null 2>&1 ); }
rebuild_py; ( cd "$src/sdks/python" && rm -rf build && SOURCE_DATE_EPOCH=1767225600 "$py" -m build --outdir "$work/py-dist1" >/dev/null 2>&1 )
run "reproducible: python wheel is byte-identical" "$work" sh -c "cmp '$work'/py-dist1/*.whl '$work'/py-dist2/*.whl"
mkdir -p "$work/ts-pack2" && ( cd "$ts" && npm pack --pack-destination "$work/ts-pack2" >/dev/null 2>&1 )
run "reproducible: npm tarball is byte-identical"  "$work" sh -c "cmp '$work'/ts-pack/*.tgz '$work'/ts-pack2/*.tgz"
run "reproducible: java jar is byte-identical"     "$jv" sh -c "cp target/nova-sdk-*[0-9].jar '$work/jar1.jar' && mvn -B -ntp -q -DskipTests clean package >/dev/null && cmp '$work/jar1.jar' target/nova-sdk-*[0-9].jar"

# ---------------------------------------------------------------- secrets
if [ -x "${GITLEAKS:-}" ]; then
  run "gitleaks: working tree" "$root" "$GITLEAKS" dir --no-banner --redact .
  run "gitleaks: git history"  "$root" "$GITLEAKS" git --no-banner --redact .
else
  skip "gitleaks" "set GITLEAKS=/path/to/gitleaks (v8.30.1); CI runs it in security.yml"
fi

printf '\n%s\n' "${summary[@]}"
echo
echo "logs: $work/logs"
exit $fail
