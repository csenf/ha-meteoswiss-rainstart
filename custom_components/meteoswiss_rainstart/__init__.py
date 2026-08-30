"""MeteoSwiss Rain-Start integration."""

from __future__ import annotations

import json
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform
from homeassistant.core import CoreState, HomeAssistant

from .const import DOMAIN
from .coordinator import MeteoSwissRainStartCoordinator
from .frontend_register import async_register_frontend

_MANIFEST = json.loads((Path(__file__).parent / "manifest.json").read_text(encoding="utf-8"))

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.IMAGE]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the bundled Lovelace card once per Home Assistant run.

    This runs once at the component level (not per config entry) so the
    card is registered exactly once even with multiple locations
    configured. Storage-mode Lovelace resources are not guaranteed to be
    loaded yet at this point, so registration itself waits for HA to
    finish starting (see frontend_register.async_register_frontend).
    """
    version = str(_MANIFEST["version"])

    async def _register(_event: object = None) -> None:
        await async_register_frontend(hass, version)

    if hass.state == CoreState.running:
        hass.async_create_task(_register())
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _register)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MeteoSwiss Rain-Start from a config entry."""
    coordinator = MeteoSwissRainStartCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload integration when config entry is updated."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
