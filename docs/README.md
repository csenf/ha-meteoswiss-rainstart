# Documentation

| Folder | Purpose |
|--------|---------|
| `what/` | Business requirements, concepts, goals |
| `how/` | Implementation plans, architecture, technical specs |

## What this integration does

Rain-start samples the MeteoSwiss precipitation radar at a pin you set. It names the device from a location name you type. The feed is unofficial website JSON (RZC measurement plus INCA rate), about 1 km cells and 5-minute steps. Official STAC and hourly local forecast are not used.

Use it to close windows before rain starts. Do not treat the rates as true millimetres per hour. They are legend lower bounds (`0.2`, `1`, `2`, …).

After you deploy Python or `manifest.json`, restart Home Assistant. Reload does not reimport modules.

## Entities

`{slug}` comes from the location name. A v1 next-rain sensor may keep the old id `sensor.meteoswiss_rainstart_next_rain_minutes`.

| Entity | What it tells you |
|--------|-------------------|
| `sensor.…_{slug}_next_rain_minutes` | Minutes until the home cell is wet. `0` if it is wet now. `unknown` if no rain falls in the horizon. |
| `binary_sensor.…_{slug}_raining` | On when the home cell meets the threshold. |
| `sensor.…_{slug}_precipitation` | Current cell rate (legend lower bound, mm/h). Not gated by the threshold. |
| `sensor.…_{slug}_nearest_rain` | Kilometres to the nearest wet blob. `0` when the home cell is wet. |
| `sensor.…_{slug}_rain_end_minutes` | Minutes until the current or next wet stretch goes dry. |
| `image.…_{slug}_intensity_graph` | Bar chart of measured (blue) and forecast (cyan) rates. |
| `sensor.…_{slug}_data_age_minutes` | Minutes since the latest radar frame, not since the last HTTP poll. |
| `sensor.…_{slug}_next_fetch` | When the coordinator will poll again. |
| `binary_sensor.…_{slug}_parser_problem` | Diagnostic. Off (`OK`) while the unofficial JSON decodes. On (`Broken`) when it does not. |

A download or network error leaves the rain sensors `unavailable`. It does not turn Parser problem on.

## When Parser problem is on

Home Assistant problem sensors are **on** when something is wrong. That is `parse_ok` false.

1. Ignore the rain sensors. They are `unavailable`. Do not trust the last ETA.
2. Open Parser problem. Read `parse_detail` and the persistent notification.
3. Open the [MeteoSwiss precipitation map](https://www.meteoschweiz.admin.ch/wetter/messwerte-und-messnetze/niederschlagsradar.html). If the map is down, wait.
4. If the map works, the unofficial JSON or legend colours likely changed. Check the Home Assistant log for `RadarParseError`.
5. Fix `radar_nowcast.py` (JSON paths, `LEGEND` colours, sanity checks). Deploy. Restart Home Assistant. Reload is not enough.
6. After a good poll the flag turns off. Dismiss the notification.

## Intensity graph

Add a Picture entity card:

```yaml
type: picture-entity
entity: image.meteoswiss_rainstart_belp_intensity_graph
show_name: true
show_state: false
```

Blue bars are measured RZC frames. Cyan bars are INCA forecast.

## Home Assistant templates

`forecast_context` lives on the next-rain sensor.

Recommended:

```
{% set ctx = state_attr('sensor.meteoswiss_rainstart_next_rain_minutes', 'forecast_context') %}
{% if ctx %}
{{ ctx.pipeline }} · {{ ctx.step_minutes }} min · until {{ ctx.window_end }}
{% else %}
unknown
{% endif %}
```

Compact:

```
{% set c = state_attr('sensor.meteoswiss_rainstart_next_rain_minutes', 'forecast_context') %}{{ c.pipeline if c else 'n/a' }} · {{ c.step_minutes if c else '?' }} min · until {{ c.window_end if c else 'n/a' }}
```

Clock time:

```
{% set ctx = state_attr('sensor.meteoswiss_rainstart_next_rain_minutes', 'forecast_context') %}
{% if ctx %}
{{ ctx.pipeline }} · {{ ctx.step_minutes }} min · until {{ as_timestamp(ctx.window_end) | timestamp_custom('%H:%M', true) }}
{% else %}
unknown
{% endif %}
```

Window bounds:

```
{% set ctx = state_attr('sensor.meteoswiss_rainstart_next_rain_minutes', 'forecast_context') %}
{% if ctx %}
{{ ctx.pipeline }} ({{ ctx.step_minutes }} min steps) · {{ ctx.window_start }} → {{ ctx.window_end }}
{% else %}
forecast_context unavailable
{% endif %}
```

## Current release

**v0.2.0** — Home Assistant custom integration `meteoswiss_rainstart`  
Install via HACS or copy `custom_components/meteoswiss_rainstart` into Home Assistant. GitHub tags and Releases are the public version. Gitea is for development; Ansible may stamp a local-only `x.y.z+dev.gSHA` on the Home Assistant copy.

| Topic | Document |
|-------|----------|
| Requirements & goals | [what/meteoswiss_rainstart_concept.md](what/meteoswiss_rainstart_concept.md) |
| Entity location naming (planned) | [what/2026-06-20-1417-entity-location-naming.md](what/2026-06-20-1417-entity-location-naming.md) |
| Entity location naming plan (v0.1.4) | [how/2026-06-20-1427-entity-location-naming-plan.md](how/2026-06-20-1427-entity-location-naming-plan.md) |
| Radar nowcast (v0.2.0) | [how/2026-08-29-1330-radar-nowcast-plan.md](how/2026-08-29-1330-radar-nowcast-plan.md) |
| Architecture & implementation | [how/2026-06-20-1400-meteoswiss-rainstart-plan.md](how/2026-06-20-1400-meteoswiss-rainstart-plan.md) |
| Pipeline/window attribute (planned 0.1.3) | [how/2026-06-20-pipeline-window-attribute-plan.md](how/2026-06-20-pipeline-window-attribute-plan.md) |
| Release history | [changelog.md](changelog.md) |

## Living documents

| File | Purpose |
|------|---------|
| `what/meteoswiss_rainstart_concept.md` | Business requirements and goals |
| `how/2026-06-20-1427-entity-location-naming-plan.md` | Implementation plan for entity location naming + map picker (v0.1.4) |
| `how/2026-06-20-1400-meteoswiss-rainstart-plan.md` | Implementation plan (updated for v0.1.2) |
| `changelog.md` | Document and release change log |
| `backlog.md` | Task tracking (add when needed) |

## Naming

Feature documents: `YYYY-MM-DD-HHmm-topic.md` in `what/` or `how/`.

## Development

Use a project virtualenv (do not install into system Python):

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest tests/ -m 'not integration'
```
