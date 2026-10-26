"""Tests for scripts/sync_openapi.py (works on temporary copies; never touches the snapshot)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "sync_openapi", ROOT / "scripts" / "sync_openapi.py"
)
sync = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sync)

SNAPSHOT = yaml.safe_load((ROOT / "openapi" / "nova-api.yaml").read_text())


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    target = tmp_path / "nova-api.yaml"
    target.write_text((ROOT / "openapi" / "nova-api.yaml").read_text())
    monkeypatch.setattr(sync, "SNAPSHOT", target)
    return target


def run(monkeypatch, *argv):
    monkeypatch.setattr("sys.argv", ["sync_openapi.py", *argv])
    return sync.main()


def test_check_passes_for_identical_content_in_json_form(
    tmp_path, isolated, monkeypatch, capsys
):
    source = tmp_path / "from-backend.json"
    source.write_text(json.dumps(SNAPSHOT))
    assert run(monkeypatch, str(source), "--check") == 0


def test_check_detects_added_removed_and_changed_operations(
    tmp_path, isolated, monkeypatch, capsys
):
    changed = json.loads(json.dumps(SNAPSHOT))
    changed["info"]["version"] = "9.9.9"
    changed["paths"].pop("/api/v1/health/")
    changed["paths"]["/api/v1/new/"] = {
        "get": {"responses": {"200": {"description": "ok"}}}
    }
    changed["paths"]["/api/v1/users/me/"]["get"]["summary"] = "changed"
    source = tmp_path / "changed.yaml"
    source.write_text(yaml.safe_dump(changed, sort_keys=False))
    assert run(monkeypatch, str(source), "--check") == 1
    out = capsys.readouterr().out
    assert (
        "+ GET /api/v1/new/" in out
        and "- GET /api/v1/health/" in out
        and "~ GET /api/v1/users/me/" in out
    )


def test_dry_run_never_writes(tmp_path, isolated, monkeypatch):
    changed = json.loads(json.dumps(SNAPSHOT))
    changed["info"]["version"] = "2.0.0"
    source = tmp_path / "changed.yaml"
    source.write_text(yaml.safe_dump(changed, sort_keys=False))
    before = isolated.read_text()
    assert run(monkeypatch, str(source), "--dry-run") == 0
    assert isolated.read_text() == before


def test_update_writes_a_valid_source(tmp_path, isolated, monkeypatch):
    changed = json.loads(json.dumps(SNAPSHOT))
    changed["info"]["version"] = "2.0.0"
    source = tmp_path / "changed.yaml"
    source.write_text(yaml.safe_dump(changed, sort_keys=False))
    assert run(monkeypatch, str(source)) == 0
    assert yaml.safe_load(isolated.read_text())["info"]["version"] == "2.0.0"


@pytest.mark.parametrize(
    "content",
    [
        "not: [valid",
        "- just\n- a list\n",
        "openapi: '2.0'\npaths: {}\n",
        "openapi: '3.0.3'\ninfo: {}\npaths: {}\n",
    ],
)
def test_invalid_sources_are_rejected_without_writing(
    tmp_path, isolated, monkeypatch, content
):
    source = tmp_path / "bad.yaml"
    source.write_text(content)
    before = isolated.read_text()
    with pytest.raises((SystemExit, Exception)):
        run(monkeypatch, str(source))
    assert isolated.read_text() == before


def test_plain_http_urls_are_refused(isolated, monkeypatch):
    with pytest.raises(SystemExit):
        run(monkeypatch, "http://example.com/nova-api.yaml")
