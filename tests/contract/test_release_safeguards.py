"""Static checks that CI never publishes: one workflow, no secrets, no cloud auth, no release steps."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"

PUBLISH_COMMANDS = [
    r"twine upload",
    r"npm publish",
    r"mvn deploy",
    r"gradle publish",
    r"pypa/gh-action-pypi-publish",
    r"google-github-actions/auth",
]


def test_there_is_exactly_one_workflow_with_secret_scan_codeql_and_tests():
    files = sorted(p.name for p in WORKFLOWS.iterdir())
    assert files == ["ci.yml"]
    jobs = yaml.safe_load((WORKFLOWS / "ci.yml").read_text())["jobs"]
    assert {"gitleaks", "codeql", "contract", "python", "typescript", "java"} == set(
        jobs
    )


def test_ci_has_no_publish_cloud_auth_secrets_or_environments():
    path = WORKFLOWS / "ci.yml"
    text = path.read_text()
    for pattern in PUBLISH_COMMANDS:
        assert not re.search(pattern, text), f"ci.yml must not contain {pattern}"
    assert "secrets." not in text
    assert "id-token" not in text
    data = yaml.safe_load(text)
    assert data["permissions"] == {"contents": "read"}
    for name, job in data["jobs"].items():
        assert "environment" not in job, name


def test_package_metadata_points_to_the_sdk_repository_and_blocks_public_upload():
    import json
    import tomllib

    pyproject = tomllib.loads((ROOT / "sdks/python/pyproject.toml").read_text())
    assert "Private :: Do Not Upload" in pyproject["project"]["classifiers"]
    pkg = json.loads((ROOT / "sdks/typescript/package.json").read_text())
    assert "publishConfig" not in pkg
    assert "require-artifact-registry" in pkg["scripts"]["prepublishOnly"]
    urls = list(pyproject["project"]["urls"].values()) + [
        pkg["homepage"],
        pkg["bugs"]["url"],
        pkg["repository"]["url"],
    ]
    assert all("infimatrix/nova-sdk" in u for u in urls), urls
    assert not any("nova-backend" in u for u in urls)
    assert (
        pyproject["project"]["name"] == "infimatrix-nova-sdk"
        and pkg["name"] == "@infimatrix/nova-sdk"
    )
