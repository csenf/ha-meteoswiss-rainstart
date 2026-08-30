"""CI stamps manifest.json on the same commit it tags."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TAG_SCRIPT = REPO_ROOT / "scripts" / "ci-tag-release.sh"
STAMP_SCRIPT = REPO_ROOT / "scripts" / "stamp-version.sh"
COMPONENT = Path("custom_components/meteoswiss_rainstart")


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def _manifest_version(repo: Path) -> str:
    path = repo / COMPONENT / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))["version"]


def _prepare_repo(tmp_path: Path, *, version: str = "0.2.0") -> Path:
    repo = tmp_path / "repo"
    origin = tmp_path / "origin.git"
    (repo / COMPONENT).mkdir(parents=True)
    (repo / "scripts").mkdir()
    shutil.copy(TAG_SCRIPT, repo / "scripts" / "ci-tag-release.sh")
    shutil.copy(STAMP_SCRIPT, repo / "scripts" / "stamp-version.sh")
    (repo / COMPONENT / "manifest.json").write_text(
        json.dumps(
            {
                "domain": "meteoswiss_rainstart",
                "name": "MeteoSwiss Rain-Start",
                "version": version,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (repo / ".gitignore").write_text("VERSION\n", encoding="utf-8")

    _git(repo.parent, "init", "--bare", str(origin))
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "chore: initial")
    _git(repo, "tag", "-a", f"v{version}", "-m", f"Release v{version}")
    _git(repo, "remote", "add", "origin", str(origin))
    _git(repo, "push", "-u", "origin", "main")
    _git(repo, "push", "origin", f"v{version}")
    return repo


def _release(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(repo / "scripts" / "ci-tag-release.sh")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


def test_feat_commit_stamps_manifest_then_tags(tmp_path: Path) -> None:
    repo = _prepare_repo(tmp_path)
    (repo / "note.txt").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "note.txt")
    _git(repo, "commit", "-m", "feat: add sensor")

    result = _release(repo)

    assert "VERSION=0.3.0" in result.stdout.splitlines()
    assert _manifest_version(repo) == "0.3.0"
    assert _git(repo, "tag", "--points-at", "HEAD").stdout.strip() == "v0.3.0"
    assert "v0.3.0" in _git(repo, "ls-remote", "--tags", "origin").stdout
    log = _git(repo, "log", "-1", "--pretty=%s").stdout.strip()
    assert log == "chore(release): v0.3.0"
    assert not (repo / COMPONENT / "VERSION").exists() or "VERSION" not in _git(
        repo, "ls-files"
    ).stdout


def test_already_tagged_head_leaves_manifest_alone(tmp_path: Path) -> None:
    repo = _prepare_repo(tmp_path)

    result = _release(repo)

    assert "VERSION=0.2.0" in result.stdout.splitlines()
    assert _manifest_version(repo) == "0.2.0"
    assert _git(repo, "tag", "--points-at", "HEAD").stdout.strip() == "v0.2.0"


def test_chore_only_does_not_release(tmp_path: Path) -> None:
    repo = _prepare_repo(tmp_path)
    (repo / "note.txt").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "note.txt")
    _git(repo, "commit", "-m", "chore: docs")

    result = _release(repo)

    assert "VERSION=0.2.0" in result.stdout.splitlines()
    assert _manifest_version(repo) == "0.2.0"
    assert _git(repo, "tag", "--points-at", "HEAD", check=False).stdout.strip() == ""


def test_fix_is_a_patch_bump(tmp_path: Path) -> None:
    repo = _prepare_repo(tmp_path)
    (repo / "note.txt").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "note.txt")
    _git(repo, "commit", "-m", "fix: parse radar")

    result = _release(repo)

    assert "VERSION=0.2.1" in result.stdout.splitlines()
    assert _manifest_version(repo) == "0.2.1"
    assert _git(repo, "tag", "--points-at", "HEAD").stdout.strip() == "v0.2.1"
