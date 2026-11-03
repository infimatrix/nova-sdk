"""Static checks that CI never publishes; only the tag-triggered release workflow may authenticate and publish."""

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


def test_there_are_exactly_the_ci_and_release_workflows():
    files = sorted(p.name for p in WORKFLOWS.iterdir())
    assert files == ["ci.yml", "release.yml"]
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


def test_release_workflow_is_manual_only_and_uses_an_approval_environment():
    data = yaml.safe_load((WORKFLOWS / "release.yml").read_text())
    triggers = data.get("on", data.get(True))
    assert set(triggers) == {"workflow_dispatch"}
    assert data["permissions"] == {"contents": "read"}
    assert "secrets." not in (WORKFLOWS / "release.yml").read_text()
    assert set(data["jobs"]) == {"python", "typescript", "java"}
    for name, job in data["jobs"].items():
        assert job["environment"] == "release", name
        assert job["permissions"] == {"contents": "read", "id-token": "write"}, name


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


def test_java_pom_cannot_deploy_unless_the_registry_profile_is_chosen():
    import xml.etree.ElementTree as ET

    ns = {"m": "http://maven.apache.org/POM/4.0.0"}
    pom = ET.parse(ROOT / "sdks/java/pom.xml").getroot()
    assert pom.find("m:distributionManagement", ns) is None
    assert pom.find("m:properties/m:maven.deploy.skip", ns).text == "true"
    profile = next(
        p
        for p in pom.findall("m:profiles/m:profile", ns)
        if p.find("m:id", ns).text == "artifact-registry"
    )
    assert profile.find("m:activation", ns) is None, "must be opt-in only"
    assert profile.find("m:properties/m:maven.deploy.skip", ns).text == "false"
    url = profile.find("m:distributionManagement/m:repository/m:url", ns).text
    assert url == "https://${ar.location}-maven.pkg.dev/${ar.project}/${ar.repository}"
    text = (ROOT / "sdks/java/pom.xml").read_text()
    for forbidden in ("repo1.maven.org", "oss.sonatype", "central.sonatype"):
        assert forbidden not in text


def test_all_three_sdks_declare_the_same_version():
    import json
    import re

    py = re.search(
        r'"([^"]+)"',
        (ROOT / "sdks/python/src/nova_sdk/_version.py")
        .read_text()
        .split("__version__")[1],
    ).group(1)
    ts = json.loads((ROOT / "sdks/typescript/package.json").read_text())["version"]
    java = re.search(
        r"<artifactId>nova-sdk</artifactId>\s*<version>([^<]+)</version>",
        (ROOT / "sdks/java/pom.xml").read_text(),
    ).group(1)
    assert py == ts == java
