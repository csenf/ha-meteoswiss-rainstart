# custom_component_ha_meteoswiss_rainstart

Deploys the MeteoSwiss Rain-Start integration to a Home Assistant host from an
orchestrator submodule checkout.

## What it does

1. Rsyncs `custom_components/meteoswiss_rainstart/` to the HA config directory
2. Resolves the release version from CI input or `git describe`
3. Writes the version into `manifest.json` (what Home Assistant displays)
4. Restarts Home Assistant when `meteoswiss_rainstart_ha_restart_command` is set

## Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `meteoswiss_rainstart_install_dir` | `/config/custom_components/meteoswiss_rainstart` | Target path on HA |
| `meteoswiss_rainstart_version` | `""` | Optional semver override |
| `meteoswiss_rainstart_ha_restart_command` | `ha core restart` | Set to `""` to skip restart |

Host-specific paths and restart commands are set in the orchestrator inventory,
not in this repository.
