# Changelog

Public history starts at **v0.2.0** (`chore: public root at v0.2.0`). Older Gitea commits stay on `archive/pre-public`.

| Date | Change |
|------|--------|
| 2026-08-30 | Lovelace card follows 2026 Home Assistant weather-card design: icon + name/state + large value, theme typography/color tokens, sections `getGridOptions`, entity suggestions, built-in config form, more-info tap, and `ha-alert` for parser problems |
| 2026-08-30 | Fix: Lovelace auto-registration checked a non-existent `lovelace.mode` attribute (the real field is `resource_mode`), so the resource was never created on any install regardless of dashboard mode; also load the resources collection before inspecting it instead of guessing via a sleep-poll loop |
| 2026-08-30 | Removed v1 config-entry migration and legacy (unslugged) entity-id support; no installs predate the public v0.2.0 root, so `_legacy_entity_id` and the coordinate-label fallback name were dead code |
| 2026-08-30 | Fix: Lovelace card now auto-registers as a resource in storage-mode dashboards; previously only the static JS was served, so the card never appeared without a manual Resources entry |
| 2026-08-30 | Gitea pulls public GitHub after promote (no `GITEA_PUSH_URL` on GitHub) |
| 2026-08-30 | Promote and release only use SemVer tags reachable from HEAD; pre-public `v0.2.1`–`v0.7.0` stay on Gitea as `archive/*` |
| 2026-08-30 | Promote to GitHub uses a write-enabled SSH deploy key (`GH_DEPLOY_KEY`) instead of a rotating PAT |
| 2026-08-30 | Promote workflow secret renamed from `GITHUB_PUSH_URL` to `GH_PUSH_URL` |
| 2026-08-30 | Promote to GitHub pushes only SemVer tags (`vMAJOR.MINOR.PATCH`) |
| 2026-08-30 | **v0.2.0 public root:** first public commit. Radar nowcast only; HACS-ready; Gitea test/promote vs GitHub tag/Release |

## v0.2.0 release notes

First public commit. This is the product on `main`, not the earlier Gitea tag that still used STAC and hourly local forecast as fallbacks.

### Added

- Home Assistant custom integration `meteoswiss_rainstart`
- Website radar nowcast (`radar_nowcast.py`) as the only rain-start source (RZC measurement + INCA rate, ~1 km cells, 5-minute steps)
- Required location name and map picker; location-aware device and entity naming
- Entities from the same nowcast: next rain, raining, precipitation, nearest rain, rain end, intensity graph, data age, next fetch, parser problem
- One-shot HA notification and recovery copy when radar JSON decode or sanity checks fail
- Hardened radar fetch (host allowlist, size cap)
- GitHub Actions stamps `manifest.json` on the tagged commit and publishes a Release
- Gitea Actions: test, optional Ansible, and `Promote to GitHub`
- Local HA deploy may stamp `x.y.z+dev.gSHA` from `scripts/dev-version.sh`
- HACS scaffold (`hacs.json`) and unit tests

### Not in this history

- Official STAC RR-INCA and hourly `local_forecast` (removed before the public root)
- Private host and HA SSH deploy
- Pre-public v0.1.x commits — see branch `archive/pre-public`

### Non-goals

- Website product remains unofficial
- Rates are legend lower bounds, not true millimetres per hour
