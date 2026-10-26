#!/usr/bin/env python3
"""Generate Java model classes from openapi/nova-api.yaml.

Output: sdks/java/src/main/java/com/infimatrix/nova/models/*.java (do not edit by hand).

* Object schemas become immutable ``record`` types annotated for Jackson. Request schemas
  (names ending in ``Request``) also get a fluent ``builder()``.
* Enum schemas become constant holders (``TenantStatusEnum.ACTIVE``); fields stay ``String`` so
  that a value added by a newer server never breaks deserialization.
* Schemas that are only sent as multipart/form data are skipped (upload endpoints take ``FileUpload``);
  binary properties of other schemas (for example an unsupported ``attachment``) are omitted.

Usage:
    scripts/gen_java_models.py          # (re)write the files
    scripts/gen_java_models.py --check  # exit 1 if the committed files are stale
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "openapi" / "nova-api.yaml"
OUT = ROOT / "sdks" / "java" / "src" / "main" / "java" / "com" / "infimatrix" / "nova" / "models"
PACKAGE = "com.infimatrix.nova.models"
BANNER = (
    "// AUTO-GENERATED from openapi/nova-api.yaml by scripts/gen_java_models.py.\n"
    "// Do not edit by hand; run the script to regenerate.\n"
)

# Envelope/transport plumbing is modelled by hand (Page, PaginationInfo, errors).
SKIP_EXACT = {"ResponseMeta", "ErrorBody", "ErrorEnvelope", "PaginationInfo"}
JAVA_RESERVED = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char", "class", "const",
    "continue", "default", "do", "double", "else", "enum", "extends", "final", "finally", "float",
    "for", "goto", "if", "implements", "import", "instanceof", "int", "interface", "long", "native",
    "new", "package", "private", "protected", "public", "return", "short", "static", "strictfp",
    "super", "switch", "synchronized", "this", "throw", "throws", "transient", "try", "void",
    "volatile", "while", "record", "var", "yield", "true", "false", "null", "builder", "equals",
    "hashCode", "toString", "getClass",
}
SCALARS = {"string": "String", "integer": "Long", "number": "Double", "boolean": "Boolean"}


def skip(name: str, schema: dict, form_only: set[str]) -> bool:
    """Skip plumbing, pages, envelopes and request schemas that are only ever sent as multipart/form data."""
    if name in SKIP_EXACT or name.endswith("Envelope") or name.startswith("Paginated"):
        return True
    return name in form_only


def form_only_schemas(spec: dict) -> set[str]:
    json_used, other_used = set(), set()
    for item in spec["paths"].values():
        for op in item.values():
            if not isinstance(op, dict):
                continue
            for content_type, media in op.get("requestBody", {}).get("content", {}).items():
                ref = ref_name(media.get("schema", {}))
                if ref:
                    (json_used if content_type == "application/json" else other_used).add(ref)
    return other_used - json_used


def ref_name(schema: dict) -> str | None:
    ref = schema.get("$ref")
    return ref.rsplit("/", 1)[-1] if ref else None


def is_enum(schema: dict) -> bool:
    return schema.get("type") == "string" and "enum" in schema and "properties" not in schema


def camel(name: str) -> str:
    parts = [p for p in re.split(r"[^0-9A-Za-z]+", name) if p]
    out = parts[0][0].lower() + parts[0][1:] if parts else "value"
    for part in parts[1:]:
        out += part[0].upper() + part[1:]
    if out[0].isdigit():
        out = "_" + out
    return out + "_" if out in JAVA_RESERVED else out


def const_name(value: str) -> str:
    name = re.sub(r"[^0-9A-Za-z]+", "_", str(value)).strip("_").upper() or "EMPTY"
    return "_" + name if name[0].isdigit() else name


def java_type(schema: dict, models: set[str], enums: set[str]) -> str:
    name = ref_name(schema)
    if name:
        if name in models:
            return name
        return "String" if name in enums else "Object"
    for key in ("allOf", "anyOf", "oneOf"):
        variants = [v for v in schema.get(key, []) if v.get("type") != "null"]
        if len(variants) == 1:
            return java_type(variants[0], models, enums)
        if variants:
            kinds = {java_type(v, models, enums) for v in variants}
            return kinds.pop() if len(kinds) == 1 else "Object"
    if "enum" in schema:
        return "String"
    kind = schema.get("type")
    if kind in SCALARS:
        return SCALARS[kind]
    if kind == "array":
        return f"List<{java_type(schema.get('items', {}), models, enums)}>"
    if kind == "object":
        return "Map<String, Object>"
    return "Object"


def doc(text: str | None, indent: str = "") -> list[str]:
    if not text:
        return []
    clean = html.escape(" ".join(text.split()), quote=False).replace("{@", "{&#64;").replace("*/", "*&#47;")
    clean = clean.replace("@", "&#64;")
    return [f"{indent}/** {clean} */"] if len(clean) < 90 else [f"{indent}/**", f"{indent} * {clean}", f"{indent} */"]


def render_enum(name: str, schema: dict) -> str:
    seen: dict[str, str] = {}
    lines = [BANNER, f"package {PACKAGE};", ""]
    lines += [f"/** Allowed values of {{@code {name}}} (kept as strings for forward compatibility). */"]
    lines.append(f"public final class {name} {{")
    for value in schema["enum"]:
        if value is None:
            continue
        const = const_name(value)
        while const in seen:
            const += "_"
        seen[const] = value
        escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'    /** The value {{@code "{html.escape(str(value), quote=False)}"}}. */')
        lines.append(f'    public static final String {const} = "{escaped}";')
    lines += ["", f"    private {name}() {{", "    }", "}", ""]
    return "\n".join(lines)


def render_record(name: str, schema: dict, models: set[str], enums: set[str]) -> str:
    required = set(schema.get("required", []))
    comps: list[tuple[str, str, str, str | None]] = []
    used: set[str] = set()
    for prop, definition in schema.get("properties", {}).items():
        if definition.get("format") == "binary":
            continue
        field = camel(prop)
        while field in used:
            field += "_"
        used.add(field)
        comps.append((prop, field, java_type(definition, models, enums), definition.get("description")))
    is_request = name.endswith("Request")
    types = " ".join(t for _, _, t, _ in comps)
    imports = []
    if "List<" in types:
        imports.append("java.util.List")
    if "Map<" in types:
        imports.append("java.util.Map")
    lines = [BANNER, f"package {PACKAGE};", ""]
    lines += [
        "import com.fasterxml.jackson.annotation.JsonIgnoreProperties;",
        "import com.fasterxml.jackson.annotation.JsonInclude;",
        "import com.fasterxml.jackson.annotation.JsonProperty;",
    ]
    lines += [f"import {i};" for i in sorted(imports)]
    lines.append("")
    summary = (schema.get("description") or f"{name} model.").strip().splitlines()[0]
    lines += ["/**", f" * {html.escape(summary, quote=False).replace('@', '&#64;').replace('*/', '*&#47;')}", " *"]
    for prop, field, _, description in comps:
        text = html.escape(" ".join((description or f"JSON property {prop}.").split()), quote=False)
        text = text.replace("@", "&#64;").replace("*/", "*&#47;")
        flag = "" if prop in required else " Optional."
        lines.append(f" * @param {field} {text}{flag}")
    lines += [" */", "@JsonIgnoreProperties(ignoreUnknown = true)", "@JsonInclude(JsonInclude.Include.NON_NULL)"]
    if comps:
        lines.append(f"public record {name}(")
        lines.append(",\n".join(f'    @JsonProperty("{prop}") {typ} {field}' for prop, field, typ, _ in comps))
        lines.append(") {")
    else:
        lines.append(f"public record {name}() {{")
    if is_request:
        lines += ["", f"    /** Returns a new builder for {{@link {name}}}. */", "    public static Builder builder() {",
                  "        return new Builder();", "    }", "",
                  f"    /** Fluent builder for {{@link {name}}}. */", "    public static final class Builder {"]
        for _, field, typ, _ in comps:
            lines.append(f"        private {typ} {field};")
        lines += ["", "        private Builder() {", "        }"]
        for prop, field, typ, _ in comps:
            lines += ["", f"        /** Sets {{@code {prop}}}. */", f"        public Builder {field}({typ} value) {{",
                      f"            this.{field} = value;", "            return this;", "        }"]
        args = ", ".join(f for _, f, _, _ in comps)
        lines += ["", f"        /** Builds the immutable request. */", f"        public {name} build() {{",
                  f"            return new {name}({args});", "        }", "    }"]
    lines += ["}", ""]
    return "\n".join(lines)


def render_all(spec: dict) -> dict[str, str]:
    schemas = spec["components"]["schemas"]
    enums = {n for n, s in schemas.items() if is_enum(s)}
    form_only = form_only_schemas(spec)
    models = {n for n, s in schemas.items() if n not in enums and not skip(n, s, form_only) and s.get("type") == "object"}
    files = {f"{n}.java": render_enum(n, schemas[n]) for n in sorted(enums)}
    files.update({f"{n}.java": render_record(n, schemas[n], models, enums) for n in sorted(models)})
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = render_all(yaml.safe_load(SPEC.read_text()))
    existing = {p.name: p for p in OUT.glob("*.java")} if OUT.exists() else {}
    if args.check:
        stale = sorted({n for n in files if n not in existing or existing[n].read_text() != files[n]}
                       | {n for n in existing if n not in files})
        if stale:
            print("Stale generated Java models: " + ", ".join(stale[:10]) + (" ..." if len(stale) > 10 else ""))
            print("Run scripts/gen_java_models.py")
            return 1
        print(f"{len(files)} generated Java models are up to date.")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for name, path in existing.items():
        if name not in files and BANNER.splitlines()[0] in path.read_text():
            path.unlink()
    for name, text in files.items():
        (OUT / name).write_text(text)
    print(f"Wrote {len(files)} files to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
