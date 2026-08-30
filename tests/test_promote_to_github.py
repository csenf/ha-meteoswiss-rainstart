"""Promote uses an SSH deploy key, not a rotating GitHub PAT."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROMOTE = REPO_ROOT / "scripts" / "promote-to-github.sh"


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
