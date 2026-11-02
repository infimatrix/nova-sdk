"""The SDK overlay (openapi/sdk-overlay.yaml) must stay small, justified and current.

The snapshot is an exact copy of the backend's contract; the overlay corrects only response shapes that a real server
was observed to send differently. If the backend later fixes its contract, the matching overlay entry becomes
redundant and ``apply_overlay`` raises, which fails these tests until the entry is deleted.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import _overlay  # noqa: E402


@pytest.fixture(scope="module")
def snapshot() -> dict:
    return _overlay.load_snapshot()


@pytest.fixture(scope="module")
def overlay() -> dict:
    return _overlay.load_overlay()


def test_overlay_applies_to_the_current_snapshot(snapshot, overlay):
    # Raises (and fails) when an entry is already satisfied by the snapshot: delete that entry then.
    merged = _overlay.apply_overlay(snapshot, overlay)
    for name in overlay.get("add_schemas", {}):
        assert name in merged["components"]["schemas"]
    for name, entry in overlay.get("add_properties", {}).items():
        assert set(entry["properties"]) <= set(merged["components"]["schemas"][name]["properties"])


def test_every_entry_states_its_evidence(overlay):
    entries = {**overlay.get("add_schemas", {}), **overlay.get("add_properties", {})}
    assert entries, "an empty overlay should be deleted together with its loader hooks"
    for name, entry in entries.items():
        assert len(str(entry.get("evidence", "")).strip()) > 40, f"{name}: say what was observed, where and when"


def test_the_overlay_cannot_change_operations_or_requests(snapshot, overlay):
    assert set(overlay) <= {"add_schemas", "add_properties"}
    merged = _overlay.apply_overlay(snapshot, overlay)
    assert merged["paths"] == snapshot["paths"]
    for name, schema in snapshot["components"]["schemas"].items():
        if name.endswith("Request"):
            assert merged["components"]["schemas"][name] == schema, f"request schema {name} must not be altered"


def test_the_snapshot_itself_is_untouched_by_applying_the_overlay(snapshot, overlay):
    before = copy.deepcopy(snapshot)
    _overlay.apply_overlay(snapshot, overlay)
    assert snapshot == before


def test_a_redundant_entry_is_rejected():
    spec = {"components": {"schemas": {"Logout": {"properties": {"message": {"type": "string"}}}}}}
    with pytest.raises(ValueError, match="already declares"):
        _overlay.apply_overlay(spec, {"add_properties": {"Logout": {"properties": {"message": {"type": "string"}}}}})
    with pytest.raises(ValueError, match="already has"):
        _overlay.apply_overlay(spec, {"add_schemas": {"Logout": {"schema": {"type": "object"}}}})
    with pytest.raises(ValueError, match="unknown schema"):
        _overlay.apply_overlay(spec, {"add_properties": {"Nope": {"properties": {"x": {}}}}})


def test_corrected_models_exist_in_every_sdk():
    assert "class TemplateRenderResult" in (ROOT / "sdks/python/src/nova_sdk/schemas.py").read_text()
    assert "export interface TemplateRenderResult" in (ROOT / "sdks/typescript/src/schemas.ts").read_text()
    java = (ROOT / "sdks/java/src/main/java/com/infimatrix/nova/models/TemplateRenderResult.java").read_text()
    assert '@JsonProperty("html_content")' in java
    webhook = (ROOT / "sdks/java/src/main/java/com/infimatrix/nova/models/WebhookEndpointCreateUpdate.java").read_text()
    assert '@JsonProperty("secret")' in webhook
