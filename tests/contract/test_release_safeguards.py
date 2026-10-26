"""Static checks that CI never publishes and releases target only Artifact Registry."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ROOT / ".github" / "workflows"
RELEASE = sorted(WORKFLOWS.glob("release-*.yml"))
ORDINARY = sorted(
    p for p in WORKFLOWS.glob("*.yml") if not p.name.startswith("release-")
)

FORBIDDEN_DESTINATIONS = [
    r"pypa/gh-action-pypi-publish",
    r"upload\.pypi\.org",
    r"test\.pypi\.org",
    r"registry\.npmjs\.org",
    r"npm\.pkg\.github\.com",
    r"repo1?\.maven\.org",
    r"oss\.sonatype",
    r"NPM_TOKEN",
    r"PYPI_",
    r"--provenance",
]
PUBLISH_COMMANDS = [
    r"twine upload",
    r"npm publish",
    r"mvn deploy",
    r"gradle publish",
    r"google-github-actions/auth",
]


def load(path):
    return yaml.safe_load(path.read_text())


def jobs(path):
    return load(path)["jobs"]


def test_there_are_release_and_ordinary_workflows():
    assert {p.name for p in RELEASE} == {"release-python.yml", "release-typescript.yml"}
    assert ORDINARY


@pytest.mark.parametrize("path", ORDINARY, ids=lambda p: p.name)
def test_ordinary_ci_has_no_publish_cloud_auth_secrets_or_environments(path):
    text = path.read_text()
    for pattern in PUBLISH_COMMANDS:
        assert not re.search(pattern, text), f"{path.name} must not contain {pattern}"
    assert "secrets." not in text
    assert "id-token" not in text
    for name, job in jobs(path).items():
        assert "environment" not in job, (path.name, name)


@pytest.mark.parametrize("path", RELEASE, ids=lambda p: p.name)
def test_release_workflows_target_only_artifact_registry(path):
    text = path.read_text()
    for pattern in FORBIDDEN_DESTINATIONS:
        assert not re.search(pattern, text), f"{path.name} must not reference {pattern}"
    assert ".pkg.dev" in text
    # project / repository / identity are externalised, never literals
    assert not re.search(r"pkg\.dev/(?!\$\{)", text)
    for var in (
        "GCP_PROJECT_ID",
        "AR_LOCATION",
        "GCP_WORKLOAD_IDENTITY_PROVIDER",
        "GCP_SERVICE_ACCOUNT",
    ):
        assert f"vars.{var}" in text
    assert "secrets." not in text, (
        "no long-lived secrets: authentication is Workload Identity Federation"
    )
    assert "credentials_json" not in text


@pytest.mark.parametrize("path", RELEASE, ids=lambda p: p.name)
def test_publish_job_is_gated_and_build_job_is_credential_free(path):
    j = jobs(path)
    build, publish = j["build"], j["publish"]
    assert (
        "id-token" not in str(build.get("permissions", {}))
        and "environment" not in build
    )
    assert (
        load(path)[True]["push"]["tags"] and "branches" not in load(path)[True]["push"]
    )
    assert publish["needs"] == "build"
    assert publish["environment"] == "artifact-registry"
    assert publish["permissions"]["id-token"] == "write"
    assert publish["permissions"]["contents"] == "read"
    condition = " ".join(str(publish["if"]).split())
    assert "github.repository == 'infimatrix/nova-sdk'" in condition
    assert "github.ref_type == 'tag'" in condition
    top = load(path).get("permissions", {})
    assert top == {"contents": "read"}, "workflow-level permissions must be read-only"


def test_dispatch_cannot_publish_unless_explicitly_requested():
    for path in RELEASE:
        inputs = load(path)[True]["workflow_dispatch"]["inputs"]
        assert inputs["publish"]["default"] is False
        assert set(inputs) == {"publish"}, "no input may select a different destination"


def test_publish_steps_only_in_publish_jobs():
    for path in RELEASE:
        for name, job in jobs(path).items():
            body = yaml.safe_dump(job)
            has = any(re.search(p, body) for p in (r"twine upload", r"npm publish"))
            assert has == (name == "publish"), (path.name, name)


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
