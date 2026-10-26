#!/usr/bin/env python3
"""Generate TypeScript model types from openapi/nova-api.yaml.

Output: sdks/typescript/src/schemas.ts (do not edit by hand).

Usage:
    scripts/gen_ts_types.py          # (re)write the file
    scripts/gen_ts_types.py --check  # exit 1 if the committed file is stale
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "openapi" / "nova-api.yaml"
TARGET = ROOT / "sdks" / "typescript" / "src" / "schemas.ts"

# Envelope/transport plumbing is modelled by hand in src/models.ts.
SKIP_EXACT = {"ResponseMeta", "ErrorBody", "ErrorEnvelope", "PaginationInfo"}
IDENT = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
SCALARS = {
    "string": "string",
    "integer": "number",
    "number": "number",
    "boolean": "boolean",
}


def skip(name: str) -> bool:
    return (
        name in SKIP_EXACT or name.endswith("Envelope") or name.startswith("Paginated")
    )


def ref_name(schema: dict) -> str | None:
    ref = schema.get("$ref")
    return ref.rsplit("/", 1)[-1] if ref else None


def ts_type(schema: dict, known: set[str]) -> str:
    name = ref_name(schema)
    if name:
        return name if name in known else "unknown"

    nullable = bool(schema.get("nullable"))
    base = _base_type(schema, known)
    return f"{base} | null" if nullable and base != "unknown" else base


def _base_type(schema: dict, known: set[str]) -> str:
    for key in ("allOf", "anyOf", "oneOf"):
        variants = [v for v in schema.get(key, []) if v.get("type") != "null"]
        if variants:
            parts = list(dict.fromkeys(ts_type(v, known) for v in variants))
            return (
                " | ".join(parts)
                if key != "allOf" or len(parts) == 1
                else " & ".join(parts)
            )
    if "enum" in schema:
        values = [v for v in schema["enum"] if v is not None]
        return " | ".join(_literal(v) for v in values) or "never"
    kind = schema.get("type")
    if kind == "string" and schema.get("format") == "binary":
        return "Binary"
    if kind in SCALARS:
        return SCALARS[kind]
    if kind == "array":
        inner = ts_type(schema.get("items", {}), known)
        return f"({inner})[]" if "|" in inner or "&" in inner else f"{inner}[]"
    if kind == "object":
        return "Record<string, unknown>"
    return "unknown"


def _literal(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def comment(text: str | None, indent: str = "") -> list[str]:
    if not text:
        return []
    lines = [ln.rstrip() for ln in text.strip().splitlines() if ln.strip()]
    lines = [ln.replace("*/", "* /") for ln in lines]
    if len(lines) == 1:
        return [f"{indent}/** {lines[0]} */"]
    return [f"{indent}/**", *[f"{indent} * {ln}" for ln in lines], f"{indent} */"]


def prop_key(name: str) -> str:
    return name if IDENT.match(name) else '"' + name.replace('"', '\\"') + '"'


def render(spec: dict) -> str:
    schemas = spec["components"]["schemas"]
    names = sorted(n for n in schemas if not skip(n))
    known = set(names)
    out = [
        "/**",
        " * Nova API types.",
        " *",
        " * AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_ts_types.py.",
        " * Do not edit by hand; run the script to regenerate.",
        " */",
        "",
        "/** A file payload accepted by upload endpoints. */",
        "export type Binary = Blob | Uint8Array | ArrayBuffer;",
    ]
    for name in names:
        schema = schemas[name]
        out.append("")
        out += comment(
            schema.get("description") if schema.get("type") != "string" else None
        )
        if "properties" in schema or (
            schema.get("type") == "object" and "enum" not in schema
        ):
            required = set(schema.get("required", []))
            out.append(f"export interface {name} {{")
            for prop, definition in schema.get("properties", {}).items():
                out += comment(definition.get("description"), "  ")
                opt = "" if prop in required else "?"
                out.append(f"  {prop_key(prop)}{opt}: {ts_type(definition, known)};")
            out.append("}")
        else:
            out.append(f"export type {name} = {ts_type(schema, known)};")
    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    out = render(yaml.safe_load(SPEC.read_text()))
    if args.check:
        if not TARGET.exists() or TARGET.read_text() != out:
            print(f"{TARGET.relative_to(ROOT)} is stale; run scripts/gen_ts_types.py")
            return 1
        print(f"{TARGET.relative_to(ROOT)} is up to date.")
        return 0
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(out)
    print(f"Wrote {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
