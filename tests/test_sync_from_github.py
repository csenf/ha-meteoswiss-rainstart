"""Gitea fast-forwards main and SemVer tags from public GitHub. No force push."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC = REPO_ROOT / "scripts" / "sync-from-github.sh"
WAIT = REPO_ROOT / "scripts" / "wait-for-github.sh"


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def _init_bare(path: Path) -> Path:
    path.mkdir(parents=True)
    subprocess.run(["git", "init", "--bare", "-b", "main", str(path)], check=True, capture_output=True)
    return path


def _seed_pair(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Gitea and GitHub start on the same v0.2.0 commit. Work clone tracks Gitea."""
    gitea = _init_bare(tmp_path / "gitea.git")
    github = _init_bare(tmp_path / "github.git")
    seed = tmp_path / "seed"
    seed.mkdir()
    _git(tmp_path, "init", "-b", "main", str(seed))
    _git(seed, "config", "user.name", "test")
    _git(seed, "config", "user.email", "test@example.com")
    (seed / "readme").write_text("public\n", encoding="utf-8")
    _git(seed, "add", ".")
    _git(seed, "commit", "-m", "chore: public root")
    _git(seed, "tag", "-a", "v0.2.0", "-m", "Release v0.2.0")
    _git(seed, "remote", "add", "gitea", str(gitea))
    _git(seed, "remote", "add", "github", str(github))
    _git(seed, "push", "gitea", "main")
    _git(seed, "push", "gitea", "v0.2.0")
    _git(seed, "push", "github", "main")
    _git(seed, "push", "github", "v0.2.0")

    work = tmp_path / "work"
    _git(tmp_path, "clone", str(gitea), str(work))
    _git(work, "config", "user.name", "test")
    _git(work, "config", "user.email", "test@example.com")
    (work / "scripts").mkdir()
    shutil.copy(SYNC, work / "scripts" / "sync-from-github.sh")
    return gitea, github, work


def _advance_github(github: Path, tmp_path: Path, *, message: str, tag: str) -> str:
    clone = tmp_path / f"gh-{tag}"
    _git(tmp_path, "clone", str(github), str(clone))
    _git(clone, "config", "user.name", "bot")
    _git(clone, "config", "user.email", "bot@example.com")
    (clone / "manifest").write_text(f"{tag}\n", encoding="utf-8")
    _git(clone, "add", "manifest")
    _git(clone, "commit", "-m", message)
    _git(clone, "tag", "-a", tag, "-m", f"Release {tag}")
    _git(clone, "push", "origin", "main")
    _git(clone, "push", "origin", tag)
    return _git(clone, "rev-parse", "HEAD").stdout.strip()


def _sync(work: Path, github: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["GH_REMOTE_URL"] = str(github)
    env["GITEA_REMOTE"] = "origin"
    return subprocess.run(
        ["bash", str(work / "scripts" / "sync-from-github.sh")],
        cwd=work,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_fast_forwards_main_and_copies_new_semver_tag(tmp_path: Path) -> None:
    gitea, github, work = _seed_pair(tmp_path)
    new_sha = _advance_github(github, tmp_path, message="chore(release): v0.3.0", tag="v0.3.0")

    result = _sync(work, github)

    assert result.returncode == 0, result.stderr
    assert _git(gitea, "rev-parse", "refs/heads/main").stdout.strip() == new_sha
    assert "v0.3.0" in _git(gitea, "tag", "-l", "v0.3.0").stdout
    assert "v0.2.0" in _git(gitea, "tag", "-l").stdout


def test_refuses_non_fast_forward_main(tmp_path: Path) -> None:
    gitea, github, work = _seed_pair(tmp_path)
    (work / "local.txt").write_text("gitea only\n", encoding="utf-8")
    _git(work, "add", "local.txt")
    _git(work, "commit", "-m", "feat: local only")
    _git(work, "push", "origin", "main")
    local_sha = _git(gitea, "rev-parse", "refs/heads/main").stdout.strip()
    _advance_github(github, tmp_path, message="chore(release): v0.3.0", tag="v0.3.0")

    result = _sync(work, github)

    assert result.returncode != 0
    assert "fast-forward" in result.stderr.lower() or "not an ancestor" in result.stderr.lower()
    assert _git(gitea, "rev-parse", "refs/heads/main").stdout.strip() == local_sha
    assert _git(gitea, "tag", "-l", "v0.3.0").stdout.strip() == ""


def test_ignores_archive_tags_on_github(tmp_path: Path) -> None:
    gitea, github, work = _seed_pair(tmp_path)
    clone = tmp_path / "gh-archive"
    _git(tmp_path, "clone", str(github), str(clone))
    _git(clone, "config", "user.name", "bot")
    _git(clone, "config", "user.email", "bot@example.com")
    _git(clone, "checkout", "--orphan", "pre-public")
    (clone / "old.txt").write_text("old\n", encoding="utf-8")
    _git(clone, "add", "old.txt")
    _git(clone, "commit", "-m", "feat: archived")
    _git(clone, "tag", "-a", "archive/v0.9.0", "-m", "old")
    _git(clone, "tag", "-a", "v0.9.0", "-m", "should not copy; not on main")
    _git(clone, "push", "origin", "v0.9.0")
    _git(clone, "push", "origin", "archive/v0.9.0")

    result = _sync(work, github)

    assert result.returncode == 0, result.stderr
    tags = _git(gitea, "tag", "-l").stdout.split()
    assert "v0.9.0" not in tags
    assert "archive/v0.9.0" not in tags
    assert "v0.2.0" in tags


def test_wait_returns_when_github_main_moves(tmp_path: Path) -> None:
    _, github, _ = _seed_pair(tmp_path)
    before = _git(github, "rev-parse", "refs/heads/main").stdout.strip()
    _advance_github(github, tmp_path, message="chore(release): v0.3.0", tag="v0.3.0")

    env = os.environ.copy()
    env["GH_REMOTE_URL"] = str(github)
    env["SINCE_SHA"] = before
    env["TIMEOUT_SECS"] = "5"
    env["INTERVAL_SECS"] = "0"
    result = subprocess.run(
        ["bash", str(WAIT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "MOVED=1" in result.stdout.splitlines()


def test_wait_times_out_when_github_unchanged(tmp_path: Path) -> None:
    _, github, _ = _seed_pair(tmp_path)
    before = _git(github, "rev-parse", "refs/heads/main").stdout.strip()

    env = os.environ.copy()
    env["GH_REMOTE_URL"] = str(github)
    env["SINCE_SHA"] = before
    env["TIMEOUT_SECS"] = "0"
    env["INTERVAL_SECS"] = "0"
    result = subprocess.run(
        ["bash", str(WAIT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "MOVED=0" in result.stdout.splitlines()
