#!/usr/bin/env bash
# Shared runner: app playbooks and roles live in this repo; inventory in ansible.
set -euo pipefail

meteoswiss_init_paths() {
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[1]}")" && pwd)"
  APP_ROOT="${APP_ROOT:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
  if [[ -z "${ANSIBLE_ROOT:-}" ]]; then
    for candidate in "${APP_ROOT}/../ansible" "${APP_ROOT}/../.."; do
      if [[ -f "${candidate}/inventories/all.yml" ]]; then
        ANSIBLE_ROOT="$(cd "${candidate}" && pwd)"
        break
      fi
    done
  fi
  ANSIBLE_ROOT="${ANSIBLE_ROOT:-$(cd "${APP_ROOT}/../ansible" && pwd)}"
}

meteoswiss_require_control_plane() {
  if [[ ! -f "${ANSIBLE_ROOT}/inventories/all.yml" ]]; then
    echo "ansible inventory not found at ANSIBLE_ROOT=${ANSIBLE_ROOT}" >&2
    echo "Clone your private ansible inventory repo beside this repo or set ANSIBLE_ROOT." >&2
    exit 1
  fi
}

meteoswiss_require_playbook() {
  local playbook_path="$1"
  if [[ ! -f "${playbook_path}" ]]; then
    echo "playbook not found: ${playbook_path}" >&2
    exit 1
  fi
}

meteoswiss_write_app_config() {
  local cfg_base
  cfg_base="$(mktemp "${TMPDIR:-/tmp}/meteoswiss-ansible-XXXXXX")"
  ANSIBLE_CONFIG="${cfg_base}.cfg"
  mv "${cfg_base}" "${ANSIBLE_CONFIG}"
  export ANSIBLE_CONFIG

  {
    echo "[defaults]"
    echo "roles_path = ${APP_ROOT}/ansible/roles"
    echo "retry_files_enabled = False"
    if [[ -f "${ANSIBLE_ROOT}/.ansible_vault_password" ]]; then
      echo "vault_password_file = ${ANSIBLE_ROOT}/.ansible_vault_password"
    fi
  } >"${ANSIBLE_CONFIG}"
}

meteoswiss_install_galaxy() {
  if [[ -f "${APP_ROOT}/ansible/galaxy-requirements.yml" ]]; then
    ansible-galaxy collection install -r "${APP_ROOT}/ansible/galaxy-requirements.yml"
  fi
}

meteoswiss_prepare_app_ansible() {
  if [[ ! -d "${APP_ROOT}/ansible/roles" ]]; then
    echo "roles not found under ${APP_ROOT}/ansible/roles" >&2
    exit 1
  fi

  if ! command -v ansible-playbook >/dev/null 2>&1; then
    echo "ansible-playbook is not on PATH" >&2
    exit 1
  fi

  meteoswiss_write_app_config
  trap '[[ -n "${ANSIBLE_CONFIG:-}" && "${ANSIBLE_CONFIG}" == *meteoswiss-ansible-* ]] && rm -f "${ANSIBLE_CONFIG}"' EXIT
  meteoswiss_install_galaxy
}

meteoswiss_run_app_playbook() {
  local playbook_rel="$1"
  shift

  meteoswiss_init_paths
  meteoswiss_require_control_plane

  local playbook_path="${APP_ROOT}/${playbook_rel}"
  meteoswiss_require_playbook "${playbook_path}"
  meteoswiss_prepare_app_ansible

  cd "${APP_ROOT}"
  ansible-playbook "${playbook_path}" \
    --inventory "${ANSIBLE_ROOT}/inventories/all.yml" \
    "$@"
}
