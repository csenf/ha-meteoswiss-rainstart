"""Rain-start binary sensors."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import translation
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import BINARY_PARSER_PROBLEM, BINARY_RAINING, DOMAIN
from .coordinator import MeteoSwissRainStartCoordinator
from .entity import RainStartEntity, assign_entity_id

_WHAT_TO_DO_FALLBACK = (
    "Ignore the rain sensors. Read parse_detail. If the MeteoSwiss "
    "precipitation map still loads, the unofficial JSON changed. Fix "
    "radar_nowcast.py, deploy, and restart Home Assistant."
)


def _resolve_what_to_do(hass: HomeAssistant) -> str:
    """Look up the localized parser_problem "what to do" hint.

    ``async_get_cached_translations`` takes a single integration domain
    (or None for "all loaded integrations"), not a set - it builds the set
    internally. Passing a set here raises ``TypeError: unhashable type``
    once the cache actually gets used, since ``{integration}`` becomes a
    set containing a set.
    """
    cached = getattr(translation, "async_get_cached_translations", None)
    if cached is None:
        return _WHAT_TO_DO_FALLBACK
    strings = cached(hass, hass.config.language, "common", DOMAIN)
    return strings.get(
        f"component.{DOMAIN}.parser_problem.what_to_do", _WHAT_TO_DO_FALLBACK
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up rain-start binary sensors."""
    coordinator: MeteoSwissRainStartCoordinator = hass.data[DOMAIN][entry.entry_id]
    raining = RainingBinarySensor(coordinator, entry)
    parser = ParserProblemBinarySensor(coordinator, entry)
    assign_entity_id(raining, entry, BINARY_RAINING, "binary_sensor")
    assign_entity_id(parser, entry, BINARY_PARSER_PROBLEM, "binary_sensor")
    async_add_entities([raining, parser])


class RainingBinarySensor(RainStartEntity, BinarySensorEntity):
    """Whether the home cell is wet at or above the configured threshold."""

    _attr_device_class = BinarySensorDeviceClass.MOISTURE
    _attr_icon = "mdi:weather-pouring"

    def __init__(self, coordinator: MeteoSwissRainStartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, BINARY_RAINING)

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.raining


class ParserProblemBinarySensor(RainStartEntity, BinarySensorEntity):
    """On when the unofficial radar JSON no longer decodes or fails sanity checks."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:alert-circle"

    def __init__(self, coordinator: MeteoSwissRainStartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, BINARY_PARSER_PROBLEM)

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return not self.coordinator.parse_ok

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        return {
            "parse_detail": self.coordinator.parse_detail,
            "last_fetch_status": self.coordinator.last_fetch_status,
            "what_to_do": _resolve_what_to_do(self.hass),
        }
