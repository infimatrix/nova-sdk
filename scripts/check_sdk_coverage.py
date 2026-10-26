#!/usr/bin/env python3
"""Measure SDK endpoint coverage against the OpenAPI contract.

Scans each SDK's source for ``("METHOD", "path")`` request calls and compares them
with the operations declared in ``openapi/nova-api.yaml``.

Exit status is non-zero when an SDK calls an operation that is not in the contract
(drift) or, with ``--strict``, when a contract operation is not implemented.

Usage:
    scripts/check_sdk_coverage.py [--sdk python|typescript|java ...] [--strict]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "openapi" / "nova-api.yaml"
EXCLUSIONS = ROOT / "openapi" / "sdk-exclusions.yaml"
METHODS = ("get", "post", "put", "patch", "delete")

# language -> (source root, file glob)
SDKS = {
    "python": (ROOT / "sdks" / "python" / "src" / "nova_sdk", "*.py"),
    "typescript": (ROOT / "sdks" / "typescript" / "src", "*.ts"),
    "java": (ROOT / "sdks" / "java" / "src" / "main" / "java", "*.java"),
}

# Matches: "GET", "tenants/{id}/"  /  "GET", f"tenants/{tid}/"  /  'GET', `tenants/${id}/`
CALL_RE = re.compile(
    r"""["'](GET|POST|PUT|PATCH|DELETE)["']\s*,\s*[fF]?["'`]([^"'`]+)["'`]"""
)


# Java: ApiRequest.of(HttpMethod.GET, "tenants/{}/", id) -> GET tenants/{}/ (bare, unquoted verb)
JAVA_CALL_RE = re.compile(r'\bHttpMethod\.(GET|POST|PUT|PATCH|DELETE)\s*,\s*"([^"]+)"')

# Matches TypeScript and Java list helpers: this.listPage<T>("tenants/", ...) -> GET tenants/
LIST_RE = re.compile(r"""listPage(?:<[^>(]*>)?\(\s*[`"']([^`"']+)[`"']""")


def collapse_template_expressions(text: str) -> str:
    """Replace each ``${...}`` interpolation (with nested braces/quotes) by ``{}``."""
    out, i = [], 0
    while i < len(text):
        if text.startswith("${", i):
            depth, j = 1, i + 2
            while j < len(text) and depth:
                depth += {"{": 1, "}": -1}.get(text[j], 0)
                j += 1
            out.append("{}")
            i = j
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def normalize(path: str) -> str:
    path = path.split("?", 1)[0].strip()
    path = re.sub(r"^/?(api/v1/)?", "", path)
    path = re.sub(r"\$?\{[^}]*\}", "{}", path)
    if path and not path.endswith("/"):
        path += "/"
    return path


def spec_operations() -> set[tuple[str, str]]:
    spec = yaml.safe_load(SPEC.read_text())
    ops = set()
    for path, item in spec["paths"].items():
        for method in METHODS:
            if method in item:
                ops.add((method.upper(), normalize(path)))
    return ops


def exclusions() -> set[tuple[str, str]]:
    data = yaml.safe_load(EXCLUSIONS.read_text()) or {}
    result = set()
    for entry in data.get("excluded", []):
        method, path = entry["operation"].split(" ", 1)
        result.add((method.upper(), normalize(path)))
    return result


def sdk_operations(language: str) -> set[tuple[str, str]]:
    root, pattern = SDKS[language]
    found = set()
    for file in root.rglob(pattern):
        source = file.read_text()
        if language == "typescript":
            source = collapse_template_expressions(source)
        pairs = JAVA_CALL_RE.findall(source) if language == "java" else CALL_RE.findall(source)
        for method, path in pairs:
            if path.strip("/").upper() in {
                *(m.upper() for m in METHODS),
                "HEAD",
                "OPTIONS",
            }:
                continue  # e.g. a frozenset of HTTP verbs, not a request
            found.add((method, normalize(path)))
        for path in LIST_RE.findall(source):
            found.add(("GET", normalize(path)))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sdk", action="append", choices=sorted(SDKS))
    parser.add_argument(
        "--strict", action="store_true", help="fail on uncovered operations"
    )
    args = parser.parse_args()

    contract = spec_operations()
    status = 0
    for language in args.sdk or sorted(SDKS):
        root, _ = SDKS[language]
        if not root.exists():
            print(f"[{language}] not present - skipped")
            continue
        implemented = sdk_operations(language)
        # PUT is covered when PATCH on the same path is implemented.
        effective = implemented | {("PUT", p) for m, p in implemented if m == "PATCH"}
        extra = sorted(implemented - contract)
        required = contract - exclusions()
        missing = sorted(required - effective)
        covered = len(required & effective)
        print(
            f"[{language}] {covered}/{len(required)} required operations covered "
            f"({100 * covered / len(required):.0f}%); "
            f"{len(contract) - len(required)} excluded"
        )
        for method, path in extra:
            print(f"  NOT IN CONTRACT: {method} {path}")
            status = 1
        for method, path in missing:
            print(f"  missing: {method} {path}")
        if args.strict and missing:
            status = 1
    return status


if __name__ == "__main__":
    sys.exit(main())
