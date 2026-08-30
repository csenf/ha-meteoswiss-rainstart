# Ansible deployment

Ansible role for deploying this integration to Home Assistant through a **private**
orchestrator repository. Hostnames, SSH keys, inventory, and workflow URLs belong
there — not in this repo.

## Role

| Role | Purpose |
|------|---------|
| `custom_component_ha_meteoswiss_rainstart` | Rsync integration files, stamp `manifest.json`, optional HA restart |

## Orchestrator integration

Your orchestrator typically:

- Mounts this repository as a git submodule
- Adds `ansible/roles` from this tree to `roles_path`
- Keeps inventory, vault, and playbooks in the orchestrator repo

See your orchestrator's own docs for paths and host names.

## Push-to-deploy (private forge only)

On the **private** copy of this repository, CI can dispatch a deploy after tests.
Set repository secrets in your forge UI — do not commit URLs or tokens:

| Secret | Purpose |
|--------|---------|
| `ANSIBLE_REPO_TOKEN` | Token allowed to trigger the orchestrator deploy workflow |
| `ANSIBLE_DISPATCH_URL` | Workflow dispatch endpoint for the orchestrator |

The public GitHub mirror should run tests only and must not hold these secrets.

Manual redeploy: use the **Deploy via Ansible (manual)** workflow on private Gitea,
if configured.
