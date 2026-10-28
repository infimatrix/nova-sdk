"""Cross-language conformance harness for the Nova SDKs.

One neutral scenario file (``scenarios.json``), one real local HTTP server and a thin driver per language.
Expectations in the scenario file are taken from the documented SDK policy (docs/conventions.md,
docs/error-handling.md, docs/authentication.md) and the OpenAPI contract, never from SDK code.

Usage::

    python tests/conformance/conformance.py --sdk python --sdk typescript --sdk java

The module is import-safe: ``check_observation`` and ``expand`` are unit-tested in ``tests/conformance/test_checker.py``
so that the checker itself is shown to reject wrong behaviour.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, unquote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


# --------------------------------------------------------------------------------------------- scenarios


def _set_path(obj, dotted: str, value) -> None:
    parts = dotted.split(".")
    for part in parts[:-1]:
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    last = parts[-1]
    if isinstance(obj, list):
        obj[int(last)] = value
    else:
        obj[last] = value


def expand(scenarios: list[dict]) -> list[dict]:
    """Expand ``variants`` (dotted-path overrides) into concrete scenarios."""
    out = []
    for scenario in scenarios:
        base = {k: v for k, v in scenario.items() if k != "variants"}
        variants = scenario.get("variants") or [{}]
        for index, overrides in enumerate(variants):
            concrete = copy.deepcopy(base)
            for dotted, value in overrides.items():
                _set_path(concrete, dotted, value)
            concrete["run_id"] = scenario["id"] if len(variants) == 1 else f"{scenario['id']}#{index}"
            out.append(concrete)
    return out


# --------------------------------------------------------------------------------------------- server


class ScriptedServer:
    """Records every request and answers from a script of steps."""

    def __init__(self, steps: list[dict]):
        self.steps = steps
        self.requests: list[dict] = []
        self._cursor = 0
        self._lock = threading.Lock()
        outer = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):
                pass

            def _handle(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                raw_path, _, raw_query = self.path.partition("?")
                record = {
                    "method": self.command,
                    "raw_path": raw_path,
                    "raw_query": raw_query,
                    "query": parse_qsl(raw_query, keep_blank_values=True),
                    "headers": {k.lower(): v for k, v in self.headers.items()},
                    "body": body,
                    "t": time.monotonic(),
                }
                step = outer._pick(record)
                if step.get("delay_ms"):
                    time.sleep(step["delay_ms"] / 1000)
                if "raw" in step:
                    payload = step["raw"].encode()
                elif "json" in step:
                    payload = json.dumps(step["json"]).encode()
                else:
                    payload = b""
                status = step.get("status", 200)
                try:
                    self.send_response(status)
                    if payload or status != 204:
                        self.send_header("Content-Type", step.get("content_type", "application/json"))
                    for name, value in (step.get("headers") or {}).items():
                        self.send_header(name, value)
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    if self.command != "HEAD":
                        self.wfile.write(payload)
                except (BrokenPipeError, ConnectionResetError):
                    pass  # client gave up (timeout scenarios)

            do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = do_HEAD = do_OPTIONS = _handle

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.httpd.daemon_threads = True
        self.httpd.handle_error = lambda *a: None  # clients that time out / reset are expected in some scenarios
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def _pick(self, record: dict) -> dict:
        with self._lock:
            self.requests.append(record)
            query = dict(record["query"])
            for step in self.steps:
                when = step.get("when_query")
                if when and all(query.get(k) == v for k, v in when.items()):
                    return step
            sequential = [s for s in self.steps if not s.get("when_query")]
            if not sequential:
                return {"status": 500, "json": {"error": "no scripted response"}}
            step = sequential[min(self._cursor, len(sequential) - 1)]
            self._cursor += 1
            return step

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()


def closed_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# --------------------------------------------------------------------------------------------- checking


def _fail(msgs: list[str], text: str) -> None:
    msgs.append(text)


def check_requests(expect: dict, recorded: list[dict], msgs: list[str]) -> None:
    if "request_count" in expect and len(recorded) != expect["request_count"]:
        _fail(msgs, f"request count {len(recorded)} != expected {expect['request_count']}")
    if "requests" in expect:
        exp_reqs = expect["requests"]
        if len(recorded) != len(exp_reqs):
            _fail(msgs, f"request count {len(recorded)} != expected {len(exp_reqs)}")
        for i, (exp, got) in enumerate(zip(exp_reqs, recorded)):
            tag = f"request[{i}]"
            if "method" in exp and got["method"] != exp["method"]:
                _fail(msgs, f"{tag} method {got['method']} != {exp['method']}")
            if "path" in exp and got["raw_path"] != exp["path"]:
                _fail(msgs, f"{tag} path {got['raw_path']!r} != {exp['path']!r}")
            for name, value in (exp.get("headers_equal") or {}).items():
                if got["headers"].get(name) != value:
                    _fail(msgs, f"{tag} header {name}={got['headers'].get(name)!r} != {value!r}")
            for name in exp.get("headers_absent") or []:
                if name in got["headers"]:
                    _fail(msgs, f"{tag} header {name} must be absent, got {got['headers'][name]!r}")
            if "user_agent_regex" in exp and not re.search(exp["user_agent_regex"], got["headers"].get("user-agent", "")):
                _fail(msgs, f"{tag} user-agent {got['headers'].get('user-agent')!r} !~ {exp['user_agent_regex']}")
            for name, value in (exp.get("query_has") or {}).items():
                values = [v for k, v in got["query"] if k == name]
                if values != [value]:
                    _fail(msgs, f"{tag} query {name}={values!r} != [{value!r}]")
            if "content_type_prefix" in exp and not got["headers"].get("content-type", "").startswith(exp["content_type_prefix"]):
                _fail(msgs, f"{tag} content-type {got['headers'].get('content-type')!r}")
            if "body_json_subset" in exp:
                try:
                    body = json.loads(got["body"].decode("utf-8"))
                except Exception as e:  # noqa: BLE001
                    _fail(msgs, f"{tag} body is not UTF-8 JSON: {e}")
                    continue
                for key, value in exp["body_json_subset"].items():
                    if body.get(key) != value:
                        _fail(msgs, f"{tag} body[{key!r}]={body.get(key)!r} != {value!r}")


def check_gaps(expected: list[list[float]], recorded: list[dict], msgs: list[str]) -> None:
    """Delays between consecutive requests (retry timing), as [min_ms, max_ms] pairs."""
    if len(recorded) < len(expected) + 1:
        _fail(msgs, f"need {len(expected) + 1} requests to check gaps, got {len(recorded)}")
        return
    for i, (lo, hi) in enumerate(expected):
        gap = (recorded[i + 1]["t"] - recorded[i]["t"]) * 1000
        if not lo <= gap <= hi:
            _fail(msgs, f"gap[{i}] {gap:.0f} ms outside [{lo}, {hi}]")


def check_path_id_invariant(inv: dict, call_id: str, recorded: list[dict], outcome: dict, msgs: list[str]) -> None:
    """Hostile ids: either rejected before sending, or sent as exactly one encoded, non-dot path segment."""
    if len(recorded) > 1:
        _fail(msgs, f"hostile id caused {len(recorded)} requests")
        return
    if not recorded:
        if outcome.get("kind") != "error" or outcome.get("category") != "Validation":
            _fail(msgs, f"no request sent but outcome is {outcome.get('kind')}/{outcome.get('category')}, not a client Validation error")
        return
    got = recorded[0]
    if got["raw_query"]:
        _fail(msgs, f"hostile id created a query string: {got['raw_query']!r}")
    path = got["raw_path"]
    prefix, suffix = inv["prefix"], inv["suffix"]
    if not (path.startswith(prefix) and path.endswith(suffix)):
        _fail(msgs, f"path {path!r} does not match {prefix}<id>{suffix}")
        return
    segment = path[len(prefix) : len(path) - len(suffix)]
    if "/" in segment:
        _fail(msgs, f"id produced extra path segment(s): {path!r}")
    if segment in (".", ".."):
        _fail(msgs, f"id became a dot-segment ({segment!r}); intermediaries/servers will normalise {path!r} away")
    if unquote(segment) != call_id:
        _fail(msgs, f"id does not round-trip: sent {segment!r} -> {unquote(segment)!r} != {call_id!r}")


def check_outcome(expect: dict, outcome: dict, msgs: list[str]) -> None:
    kind = expect["kind"]
    if kind == "ok_or_validation_without_request":
        return  # handled by the path invariant
    if outcome.get("kind") != kind:
        _fail(msgs, f"outcome kind {outcome.get('kind')!r} != {kind!r} ({outcome.get('category')}: {outcome.get('message')})")
        return
    if kind == "ok":
        if "data" in expect and outcome.get("data") != expect["data"]:
            _fail(msgs, f"data {outcome.get('data')!r} != {expect['data']!r}")
        return
    for field in ("category", "status", "code", "correlation_id", "retry_after"):
        if field in expect and outcome.get(field) != expect[field]:
            _fail(msgs, f"error {field} {outcome.get(field)!r} != {expect[field]!r}")
    message = outcome.get("message") or ""
    for needle in expect.get("message_contains") or []:
        if needle.lower() not in message.lower():
            _fail(msgs, f"error message lacks {needle!r}: {message!r}")
    for needle in expect.get("message_excludes") or []:
        if needle in message:
            _fail(msgs, f"error message leaks {needle!r}: {message!r}")
    for key in expect.get("details_keys") or []:
        if key not in (outcome.get("details_keys") or []):
            _fail(msgs, f"error details lack key {key!r}: {outcome.get('details_keys')!r}")


def check_observation(scenario: dict, outcome: dict, recorded: list[dict]) -> list[str]:
    """Return a list of violations (empty == the scenario passed)."""
    msgs: list[str] = []
    expect = scenario["expect"]
    check_requests(expect, recorded, msgs)
    if "gaps_ms" in expect:
        check_gaps(expect["gaps_ms"], recorded, msgs)
    if "path_id_invariant" in expect:
        check_path_id_invariant(expect["path_id_invariant"], scenario["call"]["id"], recorded, outcome, msgs)
    check_outcome(expect["outcome"], outcome, msgs)
    return msgs


# --------------------------------------------------------------------------------------------- drivers


def java_setup(workdir: Path) -> list[str]:
    jdk = os.environ.get("JAVA_HOME")
    java = str(Path(jdk) / "bin" / "java") if jdk else shutil.which("java")
    javac = str(Path(jdk) / "bin" / "javac") if jdk else shutil.which("javac")
    mvn = shutil.which("mvn")
    if not (java and javac and mvn):
        raise SystemExit("java/javac/mvn are required for --sdk java")
    classes = Path(os.environ.get("NOVA_CONF_JAVA_CLASSES") or ROOT / "sdks" / "java" / "target" / "classes")
    if not classes.exists():
        raise SystemExit("build the Java SDK first: (cd sdks/java && mvn -DskipTests compile)")
    cp_file = workdir / "cp.txt"
    subprocess.run(
        [mvn, "-q", "-B", "-ntp", "dependency:build-classpath", f"-Dmdep.outputFile={cp_file}", "-Dmdep.includeScope=runtime"],
        cwd=Path(os.environ.get("NOVA_CONF_JAVA_PROJECT") or ROOT / "sdks" / "java"), check=True, capture_output=True,
    )
    cp = f"{classes}{os.pathsep}{cp_file.read_text().strip()}"
    out = workdir / "javadriver"
    out.mkdir()
    subprocess.run([javac, "-cp", cp, "-d", str(out), str(HERE / "drivers" / "JavaDriver.java")], check=True)
    return [java, "-cp", f"{out}{os.pathsep}{cp}", "JavaDriver"]


def driver_command(sdk: str, workdir: Path) -> list[str]:
    if sdk == "python":
        return [os.environ.get("NOVA_CONF_PYTHON", sys.executable), str(HERE / "drivers" / "python_driver.py")]
    if sdk == "typescript":
        dist = Path(os.environ.get("NOVA_CONF_TS_DIST") or ROOT / "sdks" / "typescript" / "dist" / "index.js")
        if not dist.exists():
            raise SystemExit("build the TypeScript SDK first: (cd sdks/typescript && npm ci && npm run build)")
        return ["node", str(HERE / "drivers" / "ts_driver.mjs")]
    if sdk == "java":
        return java_setup(workdir)
    raise SystemExit(f"unknown sdk {sdk}")


def run_one(sdk: str, command: list[str], scenario: dict) -> tuple[dict, list[dict], str]:
    steps = scenario["server"]
    refused = scenario.get("server_mode") == "refused"
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith("NOVA_") or k.startswith("NOVA_CONF_")}
    with ScriptedServer(steps) as server:
        port = closed_port() if refused else server.port
        spec = {
            "base_url": f"http://127.0.0.1:{port}{scenario['client'].get('base_url_suffix', scenario.get('base_url_suffix', ''))}",
            "client": scenario["client"],
            "call": scenario["call"],
        }
        spec["client"].pop("base_url_suffix", None)
        proc = subprocess.run(
            [*command, json.dumps(spec)], capture_output=True, text=True, timeout=90, env=clean_env, check=False
        )
        recorded = list(server.requests)
    lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("{")]
    if proc.returncode != 0 or not lines:
        return {"kind": "driver_failure", "message": (proc.stderr or proc.stdout)[-600:]}, recorded, proc.stderr
    return json.loads(lines[-1]), recorded, proc.stderr


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sdk", action="append", choices=["python", "typescript", "java"])
    ap.add_argument("--only", help="substring filter on scenario run id")
    ap.add_argument("--json-out", help="write results as JSON")
    args = ap.parse_args(argv)
    sdks = args.sdk or ["python", "typescript", "java"]
    scenarios = expand(json.loads((HERE / "scenarios.json").read_text(encoding="utf-8")))
    if args.only:
        scenarios = [s for s in scenarios if args.only in s["run_id"]]
    results: dict[str, dict[str, list[str]]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for sdk in sdks:
            workdir = Path(tmp) / sdk
            workdir.mkdir()
            command = driver_command(sdk, workdir)
            for scenario in scenarios:
                outcome, recorded, _ = run_one(sdk, command, copy.deepcopy(scenario))
                if outcome.get("kind") == "driver_failure":
                    msgs = [f"driver failure: {outcome['message']}"]
                else:
                    msgs = check_observation(scenario, outcome, recorded)
                results.setdefault(scenario["run_id"], {})[sdk] = msgs
    failed = 0
    for run_id, per_sdk in results.items():
        for sdk, msgs in per_sdk.items():
            if msgs:
                failed += 1
                print(f"FAIL {run_id} [{sdk}]")
                for m in msgs:
                    print(f"     - {m}")
    total = sum(len(v) for v in results.values())
    print(f"\nconformance: {total - failed}/{total} passed ({len(results)} scenarios x {len(sdks)} sdks: {', '.join(sdks)})")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(results, indent=1))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
