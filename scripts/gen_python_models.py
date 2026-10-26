#!/usr/bin/env python3
"""Generate typed Python response models from openapi/nova-api.yaml.

Output: sdks/python/src/nova_sdk/schemas.py (do not edit by hand).

Usage:
    scripts/gen_python_models.py          # (re)write the file
    scripts/gen_python_models.py --check  # exit 1 if the committed file is stale
"""

from __future__ import annotations

import argparse
import keyword
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "openapi" / "nova-api.yaml"
TARGET = ROOT / "sdks" / "python" / "src" / "nova_sdk" / "schemas.py"

# Envelope/transport plumbing is modelled by hand in nova_sdk.models.
SKIP_EXACT = {"ResponseMeta", "ErrorBody", "ErrorEnvelope", "PaginationInfo"}
RESERVED = {"items", "keys", "values", "get", "raw", "to_dict", "from_dict"}

SCALARS = {"string": "str", "integer": "int", "number": "float", "boolean": "bool"}


def is_model(name: str, schema: dict) -> bool:
    if (
        name in SKIP_EXACT
        or schema.get("type") != "object"
        or "properties" not in schema
    ):
        return False
    return not name.endswith(("Request", "Envelope", "Enum")) and not name.startswith(
        "Paginated"
    )


def ref_name(schema: dict) -> str | None:
    ref = schema.get("$ref")
    return ref.rsplit("/", 1)[-1] if ref else None


def py_type(prop: dict, models: set[str]) -> tuple[str, tuple[str, bool] | None]:
    """Return (annotation, nested) for a property schema."""
    name = ref_name(prop)
    if name:
        return (name, (name, False)) if name in models else ("str", None)
    for key in ("allOf", "anyOf", "oneOf"):
        variants = [v for v in prop.get(key, []) if v.get("type") != "null"]
        if len(variants) == 1:
            return py_type(variants[0], models)
        if variants and all(v.get("type") == "string" for v in variants):
            return "str", None
    kind = prop.get("type")
    if kind in SCALARS:
        return SCALARS[kind], None
    if kind == "array":
        inner, nested = py_type(prop.get("items", {}), models)
        return f"list[{inner}]", (nested[0], True) if nested else None
    if kind == "object":
        return "dict[str, Any]", None
    return "Any", None


def render(spec: dict) -> str:
    schemas = spec["components"]["schemas"]
    models = {n for n, s in schemas.items() if is_model(n, s)}
    lines = [
        '"""Typed response models for the Nova API.',
        "",
        "AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_python_models.py.",
        "Do not edit by hand; run the script to regenerate.",
        "",
        "Every field is optional so that older/newer servers never break parsing;",
        "the complete payload is always available as ``model.raw``.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from dataclasses import dataclass",
        "from typing import Any, ClassVar",
        "",
        "from nova_sdk._model_base import NovaModel",
        "",
        "__all__ = [",
        *[f'    "{n}",' for n in sorted(models)],
        "]",
    ]
    for name in sorted(models):
        schema = schemas[name]
        fields, nested, aliases = [], {}, {}
        for prop_name, prop in schema["properties"].items():
            attr = prop_name
            if attr in RESERVED or keyword.iskeyword(attr):
                attr = f"{attr}_"
                aliases[attr] = prop_name
            annotation, nest = py_type(prop, models)
            if nest:
                nested[attr] = nest
            fields.append((attr, annotation, prop.get("description")))
        lines += ["", "", "@dataclass(eq=False)", f"class {name}(NovaModel):"]
        doc = (schema.get("description") or f"{name} response model.").strip()
        lines.append(f'    """{doc.splitlines()[0].replace(chr(34) * 3, "")}"""')
        lines.append("")
        if nested:
            lines.append("    _nested: ClassVar[dict[str, tuple[str, bool]]] = {")
            lines += [f'        "{k}": ("{v[0]}", {v[1]}),' for k, v in nested.items()]
            lines.append("    }")
        if aliases:
            lines.append("    _aliases: ClassVar[dict[str, str]] = {")
            lines += [f'        "{k}": "{v}",' for k, v in aliases.items()]
            lines.append("    }")
        if nested or aliases:
            lines.append("")
        for attr, annotation, _ in fields:
            lines.append(f"    {attr}: {annotation} | None = None")
        if not fields:
            lines.append("    pass")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    out = render(yaml.safe_load(SPEC.read_text()))
    if args.check:
        if not TARGET.exists() or TARGET.read_text() != out:
            print(
                f"{TARGET.relative_to(ROOT)} is stale; run scripts/gen_python_models.py"
            )
            return 1
        print(f"{TARGET.relative_to(ROOT)} is up to date.")
        return 0
    TARGET.write_text(out)
    print(f"Wrote {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
