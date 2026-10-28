"""Defect injection: prove the conformance suite notices wrong SDK behaviour.

For each defect below the script copies one SDK to a scratch directory, applies a one-line source change that
represents a plausible bug (the kind in the task brief: dropped auth header, retried POST, wrong boundary, skipped page,
ignored Retry-After, ...), builds it if necessary and runs the conformance scenarios against that copy only.
A defect is DETECTED when at least one scenario fails; an undetected defect means the suite has a blind spot.

Usage (local tool, not part of CI because it needs Maven, Node and a Python without the SDK installed in editable mode)::

    python tests/conformance/inject_defects.py --python-env /path/to/python-with-httpx --report out.json

Exit status is non-zero if any defect goes undetected.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Defect:
    id: str
    sdk: str
    file: str  # relative to sdks/<sdk>
    old: str
    new: str
    why: str
    expect_in: tuple[str, ...]  # scenario id prefixes expected to fail (informational, at least one must)
    extra: tuple[tuple[str, str, str], ...] = ()  # further (file, old, new) edits applied together with the first
    equivalent: bool = False  # True: known to be masked by a second layer, so "undetected" is the correct answer


DEFECTS = [
    # ---- Python
    Defect("PY-1", "python", "src/nova_sdk/http.py", "else (http_method in IDEMPOTENT_METHODS)", "else True",
           "POST/PATCH/DELETE retried automatically", ("C-10",)),
    Defect("PY-2", "python", "src/nova_sdk/config.py", 'headers["Authorization"] = f"Bearer {clean_key}"',
           'headers["Authorization"] = f"{clean_key}"', "Bearer scheme dropped", ("C-01", "C-02", "C-03")),
    Defect("PY-3", "python", "src/nova_sdk/http.py", "delay = self.config.retry_backoff_factor * (2**attempt)",
           "delay = self.config.retry_backoff_factor * (attempt + 1)", "backoff linear instead of doubling", ("C-11c",)),
    Defect("PY-4", "python", "src/nova_sdk/http.py", "                    retry_after = self._parse_retry_after(response)\n                    delay",
           "                    retry_after = None\n                    delay", "Retry-After ignored", ("C-12c",)),
    Defect("PY-5a", "python", "src/nova_sdk/http.py", "                if 300 <= response.status_code < 400:",
           "                if 301 <= response.status_code < 400:", "boundary in the transport only (second layer map_api_error still maps 300)",
           ("C-15",), equivalent=True),
    Defect("PY-5b", "python", "src/nova_sdk/http.py", "                if 300 <= response.status_code < 400:",
           "                if 301 <= response.status_code < 400:", "boundary: HTTP 300 not treated as redirect (both layers)", ("C-15",),
           extra=(("src/nova_sdk/exceptions.py", "    if 300 <= status_code < 400:", "    if 301 <= status_code < 400:"),)),
    Defect("PY-6", "python", "src/nova_sdk/exceptions.py",
           '            error_code=code or "AUTHENTICATION_FAILED",\n            details=details,\n            correlation_id=correlation_id,',
           '            error_code=code or "AUTHENTICATION_FAILED",\n            details=details,\n            correlation_id=None,',
           "correlation id dropped for 401", ("C-14a",)),
    Defect("PY-7", "python", "src/nova_sdk/pagination.py", "        page_number += 1", "        page_number += 2",
           "pagination skips every other page", ("C-18b",)),
    Defect("PY-8", "python", "src/nova_sdk/http.py", "        for segment in path.split(\"/\"):\n            if unquote(segment) in (\".\", \"..\"):",
           "        for segment in path.split(\"/\"):\n            if False:", "dot-segment guard removed", ("C-07a",)),
    # ---- TypeScript
    Defect("TS-1", "typescript", "src/http.ts", 'new Set(["GET", "HEAD", "OPTIONS"])', 'new Set(["GET", "HEAD", "OPTIONS", "POST"])',
           "POST retried automatically", ("C-10",)),
    Defect("TS-2", "typescript", "src/http.ts", "this.config.retryBackoffMs * 2 ** attempt", "this.config.retryBackoffMs / 2 ** attempt",
           "backoff shrinks instead of doubling", ("C-11c",)),
    Defect("TS-3a", "typescript", "src/http.ts", "if (response.status >= 300 && response.status < 400) {",
           "if (response.status > 300 && response.status < 400) {", "boundary in the transport only (second layer mapApiError still maps 300)",
           ("C-15",), equivalent=True),
    Defect("TS-3b", "typescript", "src/http.ts", "if (response.status >= 300 && response.status < 400) {",
           "if (response.status > 300 && response.status < 400) {", "boundary: HTTP 300 not treated as redirect (both layers)", ("C-15",),
           extra=(("src/errors.ts", "if (statusCode >= 300 && statusCode < 400) {", "if (statusCode > 300 && statusCode < 400) {"),)),
    Defect("TS-4", "typescript", "src/config.ts", 'headers["Authorization"] = `Bearer ${credential}`', 'headers["Authorization"] = `${credential}`',
           "Bearer scheme dropped", ("C-01", "C-02", "C-03")),
    Defect("TS-5", "typescript", "src/models.ts", "this.fetchPage(this.pagination.page + 1)", "this.fetchPage(this.pagination.page + 2)",
           "pagination skips every other page", ("C-18b",)),
    Defect("TS-6", "typescript", "src/http.ts", "Math.min(MAX_RETRY_AFTER_SECONDS, retryAfterSeconds) * 1000",
           "Math.min(MAX_RETRY_AFTER_SECONDS, retryAfterSeconds) / 1000", "Retry-After divided instead of multiplied", ("C-12c",)),
    Defect("TS-7", "typescript", "src/http.ts", "if (contentType.toLowerCase().includes(\"json\")) {", "if (false) {",
           "invalid JSON body reported as success", ("C-16a",)),
    # ---- Java
    Defect("JV-1", "java", "src/main/java/com/infimatrix/nova/http/HttpMethod.java", "return this == GET;", "return this == GET || this == POST;",
           "POST retried automatically", ("C-10",)),
    Defect("JV-2", "java", "src/main/java/com/infimatrix/nova/http/HttpTransport.java", "Math.pow(2, attempt)", "Math.pow(attempt, 2)",
           "backoff 0,1,4 instead of 1,2,4 times the base", ("C-11c",)),
    Defect("JV-3", "java", "src/main/java/com/infimatrix/nova/http/HttpTransport.java", 'headers.put("Authorization", "Bearer " + bearer);',
           'headers.put("Authorization", bearer);', "Bearer scheme dropped", ("C-01", "C-02", "C-03")),
    Defect("JV-4a", "java", "src/main/java/com/infimatrix/nova/http/HttpTransport.java", "if (status >= 300 && status < 400) {",
           "if (status > 300 && status < 400) {", "boundary in the transport only (second layer ApiErrors.map still maps 300)",
           ("C-15",), equivalent=True),
    Defect("JV-4b", "java", "src/main/java/com/infimatrix/nova/http/HttpTransport.java", "if (status >= 300 && status < 400) {",
           "if (status > 300 && status < 400) {", "boundary: HTTP 300 not treated as redirect (both layers)", ("C-15",),
           extra=(("src/main/java/com/infimatrix/nova/errors/ApiErrors.java", "if (status >= 300 && status < 400) {", "if (status > 300 && status < 400) {"),)),
    Defect("JV-5", "java", "src/main/java/com/infimatrix/nova/Page.java", "fetcher.apply(pagination.page() + 1)", "fetcher.apply(pagination.page() + 2)",
           "pagination skips every other page", ("C-18b",)),
    Defect("JV-6", "java", "src/main/java/com/infimatrix/nova/http/HttpTransport.java", "Double.parseDouble(v.trim())) * 1000", "Double.parseDouble(v.trim())) * 1",
           "Retry-After 1000x too short", ("C-12c",)),
    Defect("JV-7", "java", "src/main/java/com/infimatrix/nova/http/HttpTransport.java", 'if (stripped.equals(".") || stripped.equals(".."))', "if (false)",
           "dot-segment guard removed", ("C-07a",)),
]


def run_conformance(sdk: str, env: dict[str, str], only: str | None) -> tuple[int, str]:
    cmd = [sys.executable, str(HERE / "conformance.py"), "--sdk", sdk]
    if only:
        cmd += ["--only", only]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=1800, check=False)
    return proc.returncode, proc.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--python-env", required=True, help="python executable that has httpx but NOT nova_sdk installed")
    ap.add_argument("--sdk", action="append", choices=["python", "typescript", "java"])
    ap.add_argument("--only", help="defect id substring")
    ap.add_argument("--report")
    args = ap.parse_args()
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        for d in DEFECTS:
            if (args.sdk and d.sdk not in args.sdk) or (args.only and args.only not in d.id):
                continue
            work = Path(tmp) / d.id
            src = ROOT / "sdks" / d.sdk
            ignore = shutil.ignore_patterns("node_modules", "target", "dist", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache")
            shutil.copytree(src, work, ignore=ignore)
            bad = None
            for rel, old, new in ((d.file, d.old, d.new), *d.extra):
                target = work / rel
                text = target.read_text(encoding="utf-8")
                if text.count(old) != 1:
                    bad = f"{rel}: expected exactly one match, found {text.count(old)}"
                    break
                target.write_text(text.replace(old, new), encoding="utf-8")
            if bad:
                results.append({"id": d.id, "sdk": d.sdk, "detected": False, "equivalent": False, "bad_patch": bad})
                print(f"{d.id}: BAD PATCH ({bad})", flush=True)
                continue
            env = {k: v for k, v in os.environ.items() if not k.startswith("NOVA_")}
            if d.sdk == "python":
                env["NOVA_CONF_PYTHON"] = args.python_env
                env["PYTHONPATH"] = str(work / "src")
            elif d.sdk == "typescript":
                (work / "node_modules").symlink_to(ROOT / "sdks" / "typescript" / "node_modules")
                subprocess.run(["npx", "--no-install", "tsup"], cwd=work, check=True, capture_output=True)
                env["NOVA_CONF_TS_DIST"] = str(work / "dist" / "index.js")
            else:
                subprocess.run(["mvn", "-q", "-B", "-ntp", "-DskipTests", "compile"], cwd=work, check=True, capture_output=True)
                env["NOVA_CONF_JAVA_CLASSES"] = str(work / "target" / "classes")
                env["NOVA_CONF_JAVA_PROJECT"] = str(work)
            code, out = run_conformance(d.sdk, env, None)
            failing = sorted({line.split()[1].split("#")[0] for line in out.splitlines() if line.startswith("FAIL ")})
            detected = code != 0 and bool(failing)
            expected_hit = any(f.startswith(e) for f in failing for e in d.expect_in)
            results.append({"id": d.id, "sdk": d.sdk, "why": d.why, "detected": detected, "equivalent": d.equivalent,
                            "failing_scenarios": failing, "expected_scenario_failed": expected_hit})
            verdict = "DETECTED  " if detected else ("EQUIVALENT" if d.equivalent else "UNDETECTED")
            print(f"{d.id:6} {verdict} {d.why}: {', '.join(failing) or '-'}", flush=True)
    if args.report:
        Path(args.report).write_text(json.dumps(results, indent=1))
    missed = [r for r in results if not r.get("detected") and not r.get("equivalent")]
    equivalent = [r for r in results if r.get("equivalent") and not r.get("detected")]
    detected = [r for r in results if r.get("detected")]
    print(f"\n{len(detected)} detected, {len(equivalent)} equivalent (masked by a second layer, expected undetected), "
          f"{len(missed)} missed, of {len(results)} injected defects")
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())
