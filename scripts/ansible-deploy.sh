#!/usr/bin/env bash
# Deploy meteoswiss_rainstart to Home Assistant. Playbooks/roles here; inventory in ansible.
#
# Environment:
#   APP_ROOT, ANSIBLE_ROOT — override repo locations (default: this repo + ../ansible)
#   METEOSWISS_RAINSTART_VERSION — optional semver stamped into manifest.json
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_ansible_common.sh"

meteoswiss_init_paths
METEOSWISS_RAINSTART_VERSION="${METEOSWISS_RAINSTART_VERSION:-}"

args=(-b --tags custom_component_ha_meteoswiss_rainstart -e "meteoswiss_rainstart_repo_root=${APP_ROOT}")

if [[ -n "${METEOSWISS_RAINSTART_VERSION}" ]]; then
  args+=(-e "meteoswiss_rainstart_version=${METEOSWISS_RAINSTART_VERSION}")
fi

if [[ $# -gt 0 ]]; then
  args+=("$@")
fi

meteoswiss_run_app_playbook ansible/playbooks/deploy.yml "${args[@]}"
