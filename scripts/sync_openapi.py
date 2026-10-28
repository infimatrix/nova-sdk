#!/usr/bin/env python3
"""Update or verify the committed OpenAPI contract snapshot from a backend artifact.

The Nova backend is the source of truth for the API. It publishes its OpenAPI
document (``nova-api.yaml``) as a build artifact. This repository keeps a committed
snapshot, ``openapi/nova-api.yaml``, that the SDK generators and coverage checks use.

Usage:
    scripts/sync_openapi.py SOURCE            # validate SOURCE, show changes, update the snapshot
    scripts/sync_openapi.py SOURCE --check    # exit 1 if SOURCE differs from the snapshot
    scripts/sync_openapi.py SOURCE --dry-run  # validate and show changes without writing

SOURCE is a local file (YAML or JSON) or an ``https://`` URL.

Nothing is written unless SOURCE is a valid OpenAPI 3.x document. After an update,
regenerate and verify the SDKs (see docs/openapi-sync.md).
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

import yaml
from openapi_spec_validator import validate

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "openapi" / "nova-api.yaml"
METHODS = ("get", "post", "put", "patch", "delete")


def _display(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load(source: str) -> tuple[bytes, dict]:
    if source.startswith("https://"):
        with urllib.request.urlopen(source, timeout=30) as response:  # nosec B310 - https only, checked above
            raw = response.read()
    elif source.startswith("http://"):
        sys.exit(
            "Refusing to download the contract over plain http; use https:// or a local file."
        )
    else:
        raw = Path(source).read_bytes()
    try:
        document = yaml.safe_load(raw)  # YAML is a superset of JSON
    except yaml.YAMLError as exc:
        sys.exit(f"SOURCE is not valid YAML/JSON: {exc}")
    if not isinstance(document, dict):
        sys.exit("SOURCE does not contain an OpenAPI object.")
    return raw, document


def check_valid(document: dict) -> None:
    version = str(document.get("openapi", ""))
    if not version.startswith("3."):
        sys.exit(f"Unsupported or missing 'openapi' version: {version!r} (need 3.x).")
    validate(document)


def operations(document: dict) -> dict[tuple[str, str], dict]:
    return {
        (method.upper(), path): item[method]
        for path, item in document.get("paths", {}).items()
        for method in METHODS
        if method in item
    }


def summarize_changes(old: dict, new: dict) -> list[str]:
    before, after = operations(old), operations(new)
    lines = [f"+ {m} {p}" for m, p in sorted(after.keys() - before.keys())]
    lines += [f"- {m} {p}" for m, p in sorted(before.keys() - after.keys())]
    lines += [
        f"~ {m} {p}"
        for (m, p) in sorted(before.keys() & after.keys())
        if before[(m, p)] != after[(m, p)]
    ]
    old_v, new_v = (
        old.get("info", {}).get("version"),
        new.get("info", {}).get("version"),
    )
    if old_v != new_v:
        lines.insert(0, f"info.version: {old_v} -> {new_v}")
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "source", help="path or https URL of the backend's nova-api.yaml (or JSON)"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check", action="store_true", help="fail if SOURCE differs from the snapshot"
    )
    mode.add_argument(
        "--dry-run", action="store_true", help="validate and report changes only"
    )
    args = parser.parse_args()

    raw, document = load(args.source)
    check_valid(document)
    current = yaml.safe_load(SNAPSHOT.read_text()) if SNAPSHOT.exists() else {}
    changes = (
        summarize_changes(current, document) if current else ["(no existing snapshot)"]
    )
    identical = current == document

    if args.check:
        if identical:
            print("openapi/nova-api.yaml matches SOURCE.")
            return 0
        print("openapi/nova-api.yaml differs from SOURCE:")
        print("\n".join(f"  {line}" for line in changes) or "  (non-operation changes)")
        return 1

    print(
        f"SOURCE sha256={hashlib.sha256(raw).hexdigest()[:16]} version={document.get('info', {}).get('version')}"
    )
    print("Changes:" if not identical else "No changes.")
    for line in changes if not identical else []:
        print(f"  {line}")
    if args.dry_run or identical:
        return 0
    text = (
        raw.decode()
        if not raw.lstrip().startswith(b"{")
        else yaml.safe_dump(document, sort_keys=False, allow_unicode=True)
    )
    SNAPSHOT.write_text(text)
    print(
        f"Wrote {_display(SNAPSHOT)}. Next: regenerate SDK code and run the checks (docs/openapi-sync.md)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
