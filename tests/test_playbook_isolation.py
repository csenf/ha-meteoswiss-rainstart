"""Syntax-check local playbooks with app roles and ansible inventory."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

APP_ROOT = Path(__file__).resolve().parent.parent
ROLES_DIR = APP_ROOT / "ansible" / "roles"
PLAYBOOKS_DIR = APP_ROOT / "ansible" / "playbooks"
DEFAULT_ANSIBLE_ROOTS = (
    APP_ROOT.parent / "ansible",
    APP_ROOT.parent.parent,
)

APP_PLAYBOOKS = ("deploy.yml",)


def _ansible_root() -> Path:
    env = os.environ.get("ANSIBLE_ROOT")
    if env:
        return Path(env).resolve()
    control_plane = APP_ROOT / "control-plane"
    if control_plane.is_dir():
        return control_plane.resolve()
    for candidate in DEFAULT_ANSIBLE_ROOTS:
        if (candidate / "inventories" / "all.yml").is_file():
            return candidate.resolve()
    pytest.skip("ansible control plane not found (set ANSIBLE_ROOT or clone ../ansible)")


def _ansible_playbook() -> str:
    found = shutil.which("ansible-playbook")
    if found is None:
        pytest.skip("ansible-playbook is not on PATH")
    return found


def _syntax_check(
    playbook: Path,
    ansible_root: Path,
    tmp_path: Path,
    *,
    roles_dir: Path,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    inventory = ansible_root / "inventories" / "all.yml"
    if not inventory.is_file():
        pytest.skip(f"missing inventory {inventory}")
    if not roles_dir.is_dir():
        pytest.fail(f"missing roles directory {roles_dir}")

    cfg = tmp_path / "ansible.cfg"
    cfg.write_text(
        "[defaults]\n"
        f"roles_path = {roles_dir.resolve()}\n"
        "retry_files_enabled = False\n"
    )

    env = os.environ.copy()
    env["ANSIBLE_CONFIG"] = str(cfg)
    env.pop("ANSIBLE_ROLES_PATH", None)

    return subprocess.run(
        [
            _ansible_playbook(),
            "--syntax-check",
            "-i",
            str(inventory),
            str(playbook),
        ],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.parametrize("playbook_name", APP_PLAYBOOKS, ids=APP_PLAYBOOKS)
def test_app_playbook_parses_with_local_roles(
    playbook_name: str, tmp_path: Path
) -> None:
    ansible_root = _ansible_root()
    playbook = PLAYBOOKS_DIR / playbook_name
    if not playbook.is_file():
        pytest.fail(f"missing playbook {playbook}")

    result = _syntax_check(
        playbook, ansible_root, tmp_path, roles_dir=ROLES_DIR, cwd=APP_ROOT
    )
    assert result.returncode == 0, (
        f"{playbook_name} must parse with roles from ha-meteoswiss-rainstart\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
