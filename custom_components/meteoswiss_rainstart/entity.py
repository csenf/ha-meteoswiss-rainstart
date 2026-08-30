"""Shared coordinator entity helpers."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_LOCATION_NAME, DOMAIN, FETCH_STATUS_OK
from .coordinator import MeteoSwissRainStartCoordinator
from .location import assigned_entity_id


class RainStartEntity(CoordinatorEntity[MeteoSwissRainStartCoordinator]):
    """Device-scoped entity for one rain-start location."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: MeteoSwissRainStartCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._key = key
        self._location_name = entry.data.get(CONF_LOCATION_NAME, "MeteoSwiss Rain-Start")
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_translation_placeholders = {"location_name": self._location_name}
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": self._location_name,
            "manufacturer": "MeteoSwiss (csenf)",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_fetch_status == FETCH_STATUS_OK and super().available


def assign_entity_id(entity: RainStartEntity, entry: ConfigEntry, key: str, platform: str) -> None:
    """Set the location-slug entity_id."""
    entity_id = assigned_entity_id(entry.data, key, platform)
    if entity_id:
        entity.entity_id = entity_id
