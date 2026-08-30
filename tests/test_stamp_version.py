"""Home Assistant shows the integration version from manifest.json, not VERSION."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
STAMP = REPO_ROOT / "scripts" / "stamp-version.sh"


def _manifest(version: str = "0.0.0") -> dict:
    return {
        "domain": "meteoswiss_rainstart",
        "name": "MeteoSwiss Rain-Start",
        "version": version,
    }


def _prepare(tmp_path: Path, version: str = "0.2.0") -> Path:
    target = tmp_path / "component"
    target.mkdir()
    (target / "manifest.json").write_text(
        json.dumps(_manifest(version), indent=2) + "\n", encoding="utf-8"
    )
    return target


def _stamp(target: Path, version: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(STAMP), version, str(target)],
        capture_output=True,
        text=True,
        check=check,
    )


def test_stamp_writes_version_into_manifest_json(tmp_path: Path) -> None:
    """CI used to write VERSION only; HA Settings still showed the committed manifest."""
    target = _prepare(tmp_path, version="0.2.0")

    _stamp(target, "0.3.1")

    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "0.3.1"
    assert (target / "VERSION").read_text(encoding="utf-8") == "0.3.1\n"


def test_stamp_keeps_other_manifest_fields(tmp_path: Path) -> None:
    target = _prepare(tmp_path)
    _stamp(target, "1.0.0")

    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["domain"] == "meteoswiss_rainstart"
    assert manifest["name"] == "MeteoSwiss Rain-Start"


def test_stamp_allows_local_dev_build_metadata(tmp_path: Path) -> None:
    target = _prepare(tmp_path)
    _stamp(target, "0.2.0+dev.gabc1234")
    manifest = json.loads((target / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "0.2.0+dev.gabc1234"


@pytest.mark.parametrize("bad", ["", "v0.3.1", "0.3", "latest", "0.3.1-dev"])
def test_stamp_rejects_invalid_version(tmp_path: Path, bad: str) -> None:
    target = _prepare(tmp_path)
    result = _stamp(target, bad, check=False)
    assert result.returncode != 0
    assert json.loads((target / "manifest.json").read_text(encoding="utf-8"))["version"] == "0.2.0"


def test_stamp_requires_manifest(tmp_path: Path) -> None:
    target = tmp_path / "empty"
    target.mkdir()
    result = _stamp(target, "0.3.1", check=False)
    assert result.returncode != 0
