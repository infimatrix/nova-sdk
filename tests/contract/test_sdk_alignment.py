"""SDK/contract drift checks: every SDK must stay aligned with openapi/nova-api.yaml."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


coverage = _load("check_sdk_coverage")
models_gen = _load("gen_python_models")
ts_gen = _load("gen_ts_types")
java_gen = _load("gen_java_models")


@pytest.mark.parametrize("language", sorted(coverage.SDKS))
def test_sdk_covers_every_contract_operation(language):
    root, _ = coverage.SDKS[language]
    if not root.exists():
        pytest.skip(f"{language} SDK not present")
    contract = coverage.spec_operations()
    required = contract - coverage.exclusions()
    implemented = coverage.sdk_operations(language)
    effective = implemented | {("PUT", p) for m, p in implemented if m == "PATCH"}
    assert not (implemented - contract), (
        "SDK calls operations missing from the contract"
    )
    assert not (required - effective), (
        f"{language} SDK misses: {sorted(required - effective)}"
    )


def test_exclusions_reference_real_operations():
    contract = coverage.spec_operations()
    assert coverage.exclusions() <= contract


def test_generated_python_models_are_current():
    import yaml

    expected = models_gen.render(yaml.safe_load(models_gen.SPEC.read_text()))
    assert models_gen.TARGET.read_text() == expected, (
        "sdks/python/src/nova_sdk/schemas.py is stale; run scripts/gen_python_models.py"
    )


def test_generated_typescript_types_are_current():
    import yaml

    expected = ts_gen.render(yaml.safe_load(ts_gen.SPEC.read_text()))
    assert ts_gen.TARGET.read_text() == expected, (
        "sdks/typescript/src/schemas.ts is stale; run scripts/gen_ts_types.py"
    )


def test_generated_java_models_are_current():
    import yaml

    expected = java_gen.render_all(yaml.safe_load(java_gen.SPEC.read_text()))
    actual = {p.name: p.read_text() for p in java_gen.OUT.glob("*.java")}
    assert actual == expected, "sdks/java generated models are stale; run scripts/gen_java_models.py"
