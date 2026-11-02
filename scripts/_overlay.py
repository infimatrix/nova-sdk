"""Load the committed OpenAPI snapshot with openapi/sdk-overlay.yaml applied (used by the SDK generators)."""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "openapi" / "nova-api.yaml"
OVERLAY = ROOT / "openapi" / "sdk-overlay.yaml"


def load_snapshot() -> dict:
    return yaml.safe_load(SPEC.read_text())


def load_overlay() -> dict:
    return yaml.safe_load(OVERLAY.read_text()) or {}


def apply_overlay(spec: dict, overlay: dict) -> dict:
    """Return a copy of ``spec`` with the overlay applied. Raises if an entry does not fit the snapshot."""
    out = copy.deepcopy(spec)
    schemas = out["components"]["schemas"]
    for name, entry in (overlay.get("add_schemas") or {}).items():
        if name in schemas:
            raise ValueError(f"overlay adds schema {name!r} but the snapshot already has it; remove the overlay entry")
        schemas[name] = copy.deepcopy(entry["schema"])
    for name, entry in (overlay.get("add_properties") or {}).items():
        if name not in schemas:
            raise ValueError(f"overlay extends unknown schema {name!r}")
        props = schemas[name].setdefault("properties", {})
        for prop, definition in entry["properties"].items():
            if prop in props:
                raise ValueError(f"overlay adds {name}.{prop} but the snapshot already declares it; remove the overlay entry")
            props[prop] = copy.deepcopy(definition)
    return out


def load_spec() -> dict:
    """Snapshot + overlay: what the generators build the SDK models from."""
    return apply_overlay(load_snapshot(), load_overlay())
