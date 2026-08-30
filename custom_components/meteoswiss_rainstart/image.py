"""Nowcast intensity graph image."""

from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, IMAGE_INTENSITY
from .coordinator import MeteoSwissRainStartCoordinator
from .entity import RainStartEntity, assign_entity_id
from .intensity_graph import render_intensity_svg


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the intensity graph image."""
    coordinator: MeteoSwissRainStartCoordinator = hass.data[DOMAIN][entry.entry_id]
    entity = IntensityGraphImage(coordinator, entry, hass)
    assign_entity_id(entity, entry, IMAGE_INTENSITY, "image")
    async_add_entities([entity])


class IntensityGraphImage(RainStartEntity, ImageEntity):
    """SVG bar chart of measured + forecast intensity at the home cell."""

    _attr_content_type = "image/svg+xml"
    _attr_icon = "mdi:chart-bar"

    def __init__(
        self,
        coordinator: MeteoSwissRainStartCoordinator,
        entry: ConfigEntry,
        hass: HomeAssistant,
    ) -> None:
        RainStartEntity.__init__(self, coordinator, entry, IMAGE_INTENSITY)
        ImageEntity.__init__(self, hass)
        self._cached: bytes | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._attr_image_last_updated = datetime.now(timezone.utc)

    @callback
    def _handle_coordinator_update(self) -> None:
        self._cached = None
        self._attr_image_last_updated = datetime.now(timezone.utc)
        super()._handle_coordinator_update()

    async def async_image(self) -> bytes | None:
        if self._cached is None:
            series = ()
            if self.coordinator.data:
                series = self.coordinator.data.intensity_series
            self._cached = render_intensity_svg(series).encode("utf-8")
        return self._cached
