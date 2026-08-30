"""Diagnostics support for MeteoSwiss Rain-Start."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_LATITUDE, CONF_LONGITUDE, DOMAIN
from .coordinator import MeteoSwissRainStartCoordinator

TO_REDACT = {CONF_LATITUDE, CONF_LONGITUDE, "latitude", "longitude"}


def redact_sensitive(data: Any, keys: set[str] | None = None) -> Any:
    """Recursively replace coordinate fields before diagnostics leave the box."""
    redact = TO_REDACT if keys is None else keys
    if isinstance(data, dict):
        return {
            key: "**REDACTED**" if key in redact else redact_sensitive(value, redact)
            for key, value in data.items()
        }
    if isinstance(data, list):
        return [redact_sensitive(item, redact) for item in data]
    return data


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: MeteoSwissRainStartCoordinator = hass.data[DOMAIN][entry.entry_id]
    payload: dict[str, Any] = {
        "entry": entry.as_dict(),
        **coordinator.diagnostics_snapshot,
    }
    if coordinator.data:
        payload["last_result"] = {
            "minutes_until_rain": coordinator.data.minutes_until_rain,
            "rain_start": coordinator.data.rain_start.isoformat()
            if coordinator.data.rain_start
            else None,
            "intensity": coordinator.data.intensity,
            "source_updated": coordinator.data.source_updated.isoformat(),
            "forecast_horizon_minutes": coordinator.data.forecast_horizon_minutes,
            "forecast_context": coordinator.data.forecast_context,
        }
    return async_redact_data(redact_sensitive(payload), TO_REDACT)
