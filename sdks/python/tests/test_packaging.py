"""Guards on package metadata, exports and typing markers."""

from __future__ import annotations

import re
from pathlib import Path

import nova_sdk
from nova_sdk import NovaClient, _version

PACKAGE_DIR = Path(nova_sdk.__file__).parent


def test_version_is_single_sourced_and_semver():
    assert nova_sdk.__version__ == _version.__version__
    assert re.fullmatch(r"\d+\.\d+\.\d+([abrc.\-+]\w*)*", nova_sdk.__version__)


def test_user_agent_reports_the_package_version():
    headers = NovaClient(api_key="k").config.get_headers()
    assert headers["User-Agent"] == f"Nova-Python-SDK/{nova_sdk.__version__}"


def test_every_exported_name_resolves():
    missing = [name for name in nova_sdk.__all__ if not hasattr(nova_sdk, name)]
    assert not missing


def test_typing_marker_and_subpackages_ship():
    assert (PACKAGE_DIR / "py.typed").is_file()
    for sub in ("aio", "aio/resources", "resources"):
        assert (PACKAGE_DIR / sub / "__init__.py").is_file()


def test_generated_files_carry_do_not_edit_banners():
    for path in [
        PACKAGE_DIR / "schemas.py",
        PACKAGE_DIR / "aio" / "http.py",
        # base.py is hand-written (AsyncBaseResource); every other module is generated
        *(
            p
            for p in (PACKAGE_DIR / "aio" / "resources").glob("[!_]*.py")
            if p.name != "base.py"
        ),
    ]:
        head = path.read_text()[:400]
        assert "AUTO-GENERATED" in head, path.name


def test_sdk_does_not_import_backend_internals():
    for path in PACKAGE_DIR.rglob("*.py"):
        text = path.read_text()
        assert not re.search(
            r"^\s*(from|import)\s+(django|rest_framework|apps)\b", text, re.M
        ), path
