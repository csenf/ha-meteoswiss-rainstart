"""Local HA deploys stamp base+dev.gSHA; a tagged release stays plain SemVer."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEV_VERSION = REPO_ROOT / "scripts" / "dev-version.sh"
COMPONENT = Path("custom_components/meteoswiss_rainstart")


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def _prepare(tmp_path: Path, *, version: str = "0.2.0") -> Path:
    repo = tmp_path / "repo"
    (repo / COMPONENT).mkdir(parents=True)
    (repo / "scripts").mkdir()
    shutil.copy(DEV_VERSION, repo / "scripts" / "dev-version.sh")
    (repo / COMPONENT / "manifest.json").write_text(
        json.dumps({"domain": "meteoswiss_rainstart", "version": version}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    _git(repo.parent, "init", "-b", "main", str(repo))
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "chore: initial")
    _git(repo, "tag", "-a", f"v{version}", "-m", f"Release v{version}")
    return repo


def _dev_version(repo: Path) -> str:
    result = subprocess.run(
        ["bash", str(repo / "scripts" / "dev-version.sh")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [line for line in result.stdout.splitlines() if line.startswith("VERSION=")]
    assert lines, result.stdout
    return lines[-1].split("=", 1)[1]


def test_on_release_tag_prints_plain_semver(tmp_path: Path) -> None:
    repo = _prepare(tmp_path)
    assert _dev_version(repo) == "0.2.0"


def test_after_tag_prints_dev_build(tmp_path: Path) -> None:
    repo = _prepare(tmp_path)
    (repo / "note.txt").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "note.txt")
    _git(repo, "commit", "-m", "feat: wip")
    sha = _git(repo, "rev-parse", "--short=7", "HEAD").stdout.strip()
    assert _dev_version(repo) == f"0.2.0+dev.g{sha}"
