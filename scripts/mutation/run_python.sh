#!/usr/bin/env bash
# mutmut on the handwritten Python transport. Usage: scripts/mutation/run_python.sh [workdir]
set -euo pipefail
root="$(cd "$(dirname "$0")/../.." && pwd)"
work="${1:-$(mktemp -d)}"
mkdir -p "$work"
rm -rf "$work/py" && cp -r "$root/sdks/python" "$work/py"
cd "$work/py"
# mutmut only sees mutated code if the SDK is imported from the mutated copy, so use a venv WITHOUT an editable install.
python3 -m venv "$work/venv"
"$work/venv/bin/pip" -q install httpx pytest hypothesis anyio mutmut
cat >> pyproject.toml <<'EOF'

[tool.mutmut]
source_paths = ["src/nova_sdk/http.py", "src/nova_sdk/config.py", "src/nova_sdk/pagination.py", "src/nova_sdk/exceptions.py"]
also_copy = ["tests/", "src/"]
EOF
sed -i 's/^testpaths = \["tests"\]/testpaths = ["tests"]\npythonpath = ["src"]/; s/^addopts = .*/addopts = "--tb=short -q -p no:cacheprovider"/' pyproject.toml
"$work/venv/bin/mutmut" run || true
"$work/venv/bin/mutmut" results --all true | awk -F': ' '{print $2}' | sort | uniq -c
echo "survivors: cd $work/py && $work/venv/bin/mutmut results ; mutmut show <name>"
