# Ansible deployment

This repo owns the deploy playbook, Ansible role, and integration source.
The [ansible orchestrator](https://git.qwsd.de/csenf/ansible) supplies inventory
only (`hass` group → `homeassistant.local`, SSH as root).

## Deploy

Clone both repos as siblings (`~/Developer/ansible` + `~/Developer/ha-meteoswiss-rainstart`):

```bash
./scripts/ansible-deploy.sh
```

Optional: `METEOSWISS_RAINSTART_VERSION=1.2.3 ./scripts/ansible-deploy.sh`  
Local dev version (no override): uses `scripts/dev-version.sh` → `x.y.z+dev.gSHA` on the HA copy.

Host overrides: `inventories/host_vars/homeassistant.local/vars.yml` in the ansible repo
(`meteoswiss_rainstart_install_dir`, `meteoswiss_rainstart_ha_restart_command`).

## Layout

```text
ansible/
├── playbooks/deploy.yml
└── roles/custom_component_ha_meteoswiss_rainstart/
```

## CI deploy

**Gitea `main`:** tests only (no auto-tag — public semver tags live on GitHub).

When a **`v*.*.*` tag** exists on this repo (e.g. after **Promote to GitHub** syncs back),
`release.yml` runs tests then deploys **from that tag** via `.gitea/workflows/deploy.yml`.

Manual redeploy: **Deploy via Ansible (manual)**, optional version input.

## Gitea secrets (deploy)

| Secret | Purpose |
|--------|---------|
| `ANSIBLE_REPO_TOKEN` | Clone private ansible repo in CI |
| `HA_SSH_KEY` | SSH deploy key for Home Assistant |
| `ANSIBLE_VAULT_PASSWORD` | If vault vars are added later |
| `SSH_KNOWN_HOSTS` | Optional; CI also runs `ssh-keyscan homeassistant.local` |

Promote / GitHub mirror secrets (`GH_DEPLOY_KEY`, etc.) are separate — see root `AGENTS.md`.
