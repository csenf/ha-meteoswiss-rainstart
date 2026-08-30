# Changelog

| Date | Change |
|------|--------|
| 2026-08-30 | Split Gitea (test + optional Ansible) from GitHub (tag + Release); local HA deploys may stamp `x.y.z+dev.gSHA` |
| 2026-08-30 | CI stamps `manifest.json` on the tagged commit and publishes a GitHub Release so HA and HACS stay aligned |
| 2026-08-30 | Drop private host and HA SSH deploy from the repo so the integration can be published (HACS / GitHub Actions) |
| 2026-08-29 | Harden radar fetch (host allowlist, size cap), wire HA migrate/options hooks, drop leftover local-forecast façade, add helper tests |
| 2026-08-29 | Add Parser problem recovery steps to setup copy, the notification, and living docs |
| 2026-08-29 | Add `parser_problem` binary (stays available) plus a one-shot HA notification when radar JSON decode/sanity fails |
| 2026-08-29 | Add data-age (radar frame minutes) and next-fetch timestamp sensors |
| 2026-08-29 | Add raining, precipitation, nearest rain, rain end, and intensity graph image from the same radar nowcast |
| 2026-08-29 | Radar nowcast is the only rain-start source; drop STAC RR-INCA and hourly `local_forecast`; location name is required |
| 2026-08-29 | CI deploy now stamps `manifest.json` version (HA reads that, not the `VERSION` file) |
| 2026-08-29 | **v0.2.0 released:** website radar nowcast (RZC + INCA, 5 min) is the primary rain-start pipeline; STAC then local hourly remain fallbacks |
| 2026-06-20 | **v0.1.4 released:** map picker (LocationSelector), persisted `location_name`, location-aware device/entity naming (Next rain in Belp), v2 migration |
| 2026-06-20 | **v0.1.3 released:** `forecast_context` sensor attribute (pipeline, collection, parameter, step_minutes, window_start/end) |
| 2026-06-20 | **v0.1.2 released:** local-forecast fallback, `h5netcdf`, docs updated to match implementation |
| 2026-06-20 | **v0.1.1:** replace `netcdf4` with `h5netcdf` for Home Assistant Core container compatibility |
| 2026-06-20 | **v0.1.0:** initial integration — config flow, sensor, coordinator, diagnostics, deploy script, unit tests |
| 2026-06-20 | Aligned concept and plan documents; closed documentation gaps |
| 2026-06-20 | Initial documentation structure and implementation plan |

## v0.2.0 release notes

### Added
- `radar_nowcast.py` — sample MeteoSwiss precipitation website JSON (RZC measurement + INCA rate) at the configured LV95 cell
- `DATA_SOURCE_RADAR` / `PIPELINE_RADAR` (`radar_nowcast`, 5-minute steps)
- Sensor attribute `radar_time` (last RZC frame clock; do not call it "now")
- Unit tests: `tests/test_radar_nowcast.py`
- Plan: `docs/how/2026-08-29-1330-radar-nowcast-plan.md`

### Changed
- `fetch_rain_start()` order: website radar → STAC RR-INCA → local hourly CSV
- Upgrade notification also fires when leaving `local_forecasting` for `radar_nowcast`
- `manifest.json` version → 0.2.0

### Non-goals
- No second entity (same `next_rain_minutes` sensor)
- No rain-end sensor
- Website product remains unofficial

## v0.1.4 release notes

### Added
- Map picker via `selector.LocationSelector` in initial config and options flow (DRY `build_setup_schema`)
- `location.py` with `slugify_location_name`, `format_coordinate_label`, `parse_location_from_input`, `resolve_location_name*`, `entity_id_for_location`
- `CONF_LOCATION`, `CONF_LOCATION_NAME` constants
- `location_name` resolved at setup: user-provided > nearest forecast point name > "lat, lon"
- Dynamic entity name using translation placeholder: "Next rain in {location_name}"
- Device name set to resolved `location_name`
- `location_name` exposed in sensor `extra_state_attributes` and coordinator diagnostics
- New entity_id convention for fresh v0.1.4+ installs: `sensor.meteoswiss_rainstart_{slug}_next_rain_minutes`
- Options flow (`MeteoSwissRainStartOptionsFlow`) allowing coordinate + name change
- `async_migrate_entry` for v1 → v2 (adds `location_name`, sets legacy flag for entity_id preservation)
- Unit tests: `tests/test_location.py`, `tests/test_config_flow.py`
- German translations updated

### Changed
- Config entry `VERSION = 2`
- `async_step_user` uses map selector + name resolution; stores `latitude`/`longitude` + `location_name` + threshold/poll
- Sensor `__init__` uses entry `location_name` for device name and placeholders; `_attr_name` removed in favor of translation
- `async_setup_entry` sets per-location `entity_id` (legacy preserved for migrated entries)
- `manifest.json` version → 0.1.4
- Existing v1 entries keep their `sensor.meteoswiss_rainstart_next_rain_minutes` entity_id

### Non-goals (per plan)
- No external geocoding (Nominatim)
- Coordinator poll / api.py unchanged
- No change to entity_id for pre-existing entries

## v0.1.3 release notes

### Added
- New `forecast_context` attribute on the sensor (and `RainStartResult`) exposing `pipeline`, `collection`, `parameter`, `step_minutes`, `window_start`, `window_end`, and optional `forecast_point` / `intensity_unit`
- `PIPELINE_NOWCASTING` and `PIPELINE_LOCAL` presets in `const.py`
- `build_forecast_context()` helper (computes window bounds from the same `times` array used for rain scan)
- Unit tests: `test_build_forecast_context_nowcasting`, `test_build_forecast_context_local`, `test_horizon_matches_window`
- Diagnostics now includes `forecast_context`

### Changed
- `fetch_rain_start_from_dataset` and local fallback now populate `forecast_context`
- `extra_state_attributes` and diagnostics snapshot surface the new attribute
- `manifest.json` version → 0.1.3

### Non-goals (per plan)
- No removal of legacy `data_source` / `forecast_point`
- No new entities

## v0.1.2 release notes

### Added
- `local_forecast.py` — fallback using MeteoSwiss local point forecasting (`ch.meteoschweiz.ogd-local-forecasting`) when nowcasting grid assets are not published on STAC
- Sensor attributes `data_source` and `forecast_point`
- Diagnostics fields `data_source` and `forecast_point`
- Unit tests in `tests/test_local_forecast.py`
- Python venv dev workflow via `requirements-dev.txt` and `.gitignore`

### Changed
- `fetch_rain_start()` tries nowcasting NetCDF first, then local forecast CSV
- NetCDF reader prefers `h5netcdf` engine (falls back to `netcdf4` in dev venv)
- Entity id fixed to `sensor.meteoswiss_rainstart_next_rain_minutes`

### Known at release
- STAC collection `ch.meteoschweiz.ogd-nowcasting` has items but **no `RR-INCA` assets yet** — production runs use `data_source: local_forecasting` (hourly resolution)
- Window group added in HA `configuration.yaml`; rain automation YAML still needs manual update (disable legacy automation `1778493348393`)
