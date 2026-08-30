"""Promote uses an SSH deploy key and only SemVer tags reachable from HEAD."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMOTE = REPO_ROOT / "scripts" / "promote-to-github.sh"
REACHABLE = REPO_ROOT / "scripts" / "reachable-semver-tags.sh"


def _run(env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        ["bash", str(PROMOTE)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=merged,
        check=False,
    )


def test_promote_requires_deploy_key() -> None:
    result = _run({"GH_DEPLOY_KEY": ""})
    assert result.returncode != 0
    assert "GH_DEPLOY_KEY" in result.stderr


def test_promote_rejects_invalid_key() -> None:
    result = _run({"GH_DEPLOY_KEY": "not-a-key"})
    assert result.returncode != 0
    assert "passphrase-free" in result.stderr or "not a valid" in result.stderr


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def test_reachable_semver_tags_skips_pre_public_leftovers(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "scripts").mkdir(parents=True)
    shutil.copy(REACHABLE, repo / "scripts" / "reachable-semver-tags.sh")
    (repo / "readme").write_text("public\n", encoding="utf-8")
    _git(repo.parent, "init", "-b", "main", str(repo))
    _git(repo, "config", "user.name", "test")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "chore: public root")
    _git(repo, "tag", "-a", "v0.2.0", "-m", "Release v0.2.0")
    _git(repo, "tag", "-a", "archive/v0.2.0", "-m", "old public-looking tag name")

    _git(repo, "checkout", "--orphan", "pre-public")
    (repo / "old.txt").write_text("old\n", encoding="utf-8")
    _git(repo, "add", "old.txt")
    _git(repo, "commit", "-m", "feat: archived")
    _git(repo, "tag", "-a", "v0.7.0", "-m", "Release v0.7.0")
    _git(repo, "checkout", "main")
    _git(repo, "branch", "-D", "pre-public")

    listed = subprocess.run(
        ["bash", str(repo / "scripts" / "reachable-semver-tags.sh")],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    assert listed.stdout.splitlines() == ["v0.2.0"]
    assert "reachable-semver-tags.sh" in PROMOTE.read_text(encoding="utf-8")
