# MeteoSwiss Rain-Start

Home Assistant custom integration that estimates when rain will start at a pin in Switzerland. Use it to close windows before rain arrives.

It samples the unofficial MeteoSwiss precipitation radar JSON (RZC measurement plus INCA rate) at about 1 km cells and 5-minute steps. Official STAC and hourly local forecast are not used. Rates are legend lower bounds (`0.2`, `1`, `2`, …), not true millimetres per hour.

## Install

### HACS (recommended)

1. Add this repository as a custom repository in [HACS](https://hacs.xyz/) (type **Integration**).
2. Search for **MeteoSwiss Rain-Start** and install it.
3. Restart Home Assistant.
4. Add the integration under **Settings → Devices & services**.

### Manual

Copy `custom_components/meteoswiss_rainstart` into your Home Assistant `custom_components` folder, then restart.

## Setup

Type a location name and set the pin on the map. That name labels the device. After you change Python or `manifest.json`, restart Home Assistant. Reload does not reimport modules.

## Entities

`{slug}` comes from the location name.

| Entity | What it tells you |
|--------|-------------------|
| `sensor.…_{slug}_next_rain_minutes` | Minutes until the home cell is wet. `0` if it is wet now. `unknown` if no rain falls in the horizon. |
| `binary_sensor.…_{slug}_raining` | On when the home cell meets the threshold. |
| `sensor.…_{slug}_precipitation` | Current cell rate (legend lower bound, mm/h). |
| `sensor.…_{slug}_nearest_rain` | Kilometres to the nearest wet blob. `0` when the home cell is wet. |
| `sensor.…_{slug}_rain_end_minutes` | Minutes until the current or next wet stretch goes dry. |
| `image.…_{slug}_intensity_graph` | Bar chart of measured (blue) and forecast (cyan) rates. |
| `sensor.…_{slug}_data_age_minutes` | Minutes since the latest radar frame, not since the last HTTP poll. |
| `sensor.…_{slug}_next_fetch` | When the coordinator will poll again. |
| `binary_sensor.…_{slug}_parser_problem` | Diagnostic. Off (`OK`) while the unofficial JSON decodes. On (`Broken`) when it does not. |

A download or network error leaves the rain sensors `unavailable`. It does not turn Parser problem on.

## Lovelace card

The integration registers its bundled card as a Lovelace resource automatically (storage-mode dashboards, the default). After installing or updating, restart Home Assistant, then add a card to your dashboard:

```yaml
type: custom:meteoswiss-rainstart-card
entity: sensor.meteoswiss_rainstart_belp_next_rain_minutes
```

The card reads the next-rain sensor and discovers the related entities for the same location. It follows the Home Assistant weather-card layout: condition icon, location, status, a large minutes value, a measured/forecast timeline, and labeled stats (current rate, rain end, radar age). Parser problem uses a Home Assistant error alert. In the sections view the card defaults to full width (12 columns). Tapping it opens more-info for the next-rain sensor. The card picker suggests it for that sensor (Home Assistant 2026.6+).

### If the card is not in the card picker

- Auto-registration only works for **storage-mode** dashboards (the default). If your dashboard is defined in `configuration.yaml` (`lovelace: mode: yaml`), add the resource by hand:

  ```yaml
  lovelace:
    resources:
      - url: /meteoswiss_rainstart/frontend/rainstart-card.js
        type: module
  ```

- Auto-registration runs once Home Assistant has fully started. If the resource is missing right after a fresh install, restart Home Assistant once more.
- After an update, hard-refresh the browser (or clear the app cache on the Companion App) if the card keeps rendering the previous version.

## When Parser problem is on

1. Ignore the rain sensors. They are `unavailable`.
2. Open Parser problem and read `parse_detail`.
3. Check the [MeteoSwiss precipitation map](https://www.meteoschweiz.admin.ch/wetter/messwerte-und-messnetze/niederschlagsradar.html). If the map is down, wait.
4. If the map works, the unofficial JSON or legend likely changed. Check the Home Assistant log for `RadarParseError`.

## Intensity graph

```yaml
type: picture-entity
entity: image.meteoswiss_rainstart_belp_intensity_graph
show_name: true
show_state: false
```

## Development

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest tests/ -m 'not integration'
```

To copy the integration into a local Home Assistant config:

```bash
./scripts/deploy.sh /path/to/homeassistant/custom_components/meteoswiss_rainstart
```

More detail: [docs/README.md](docs/README.md).
