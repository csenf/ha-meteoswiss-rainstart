"""Rain-start sensors."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength, UnitOfTime, UnitOfVolumetricFlux
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    SENSOR_DATA_AGE,
    SENSOR_KEY,
    SENSOR_NEAREST_RAIN,
    SENSOR_NEXT_FETCH,
    SENSOR_PRECIPITATION,
    SENSOR_RAIN_END,
)
from .coordinator import MeteoSwissRainStartCoordinator
from .entity import RainStartEntity, assign_entity_id
from .timing import data_age_minutes, next_fetch_at


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up rain-start sensors."""
    coordinator: MeteoSwissRainStartCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[RainStartEntity] = [
        NextRainSensor(coordinator, entry),
        PrecipitationSensor(coordinator, entry),
        NearestRainSensor(coordinator, entry),
        RainEndSensor(coordinator, entry),
        DataAgeSensor(coordinator, entry),
        NextFetchSensor(coordinator, entry),
    ]
    keys = (
        SENSOR_KEY,
        SENSOR_PRECIPITATION,
        SENSOR_NEAREST_RAIN,
        SENSOR_RAIN_END,
        SENSOR_DATA_AGE,
        SENSOR_NEXT_FETCH,
    )
    for entity, key in zip(entities, keys, strict=True):
        assign_entity_id(entity, entry, key, "sensor")
    async_add_entities(entities)


class NextRainSensor(RainStartEntity, SensorEntity):
    """Minutes until rain starts at the configured location."""

    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:weather-rainy"

    def __init__(self, coordinator: MeteoSwissRainStartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, SENSOR_KEY)

    @property
    def native_value(self) -> int | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.minutes_until_rain

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        data = self.coordinator.data
        if not data:
            attrs: dict[str, object] = {
                "threshold_mm": self.coordinator.threshold,
                "latitude": self.coordinator.latitude,
                "longitude": self.coordinator.longitude,
            }
        else:
            attrs = {
                "rain_start": data.rain_start.isoformat() if data.rain_start else None,
                "intensity": data.intensity,
                "source_updated": data.source_updated.isoformat(),
                "forecast_horizon_minutes": data.forecast_horizon_minutes,
                "data_source": data.data_source,
                "forecast_context": data.forecast_context,
                "radar_time": (data.forecast_context or {}).get("radar_time"),
                "threshold_mm": self.coordinator.threshold,
                "latitude": self.coordinator.latitude,
                "longitude": self.coordinator.longitude,
            }
        attrs["location_name"] = self._location_name
        return attrs


class PrecipitationSensor(RainStartEntity, SensorEntity):
    """Current cell precipitation rate (legend lower bound, mm/h)."""

    _attr_device_class = SensorDeviceClass.PRECIPITATION_INTENSITY
    _attr_native_unit_of_measurement = UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:water"

    def __init__(self, coordinator: MeteoSwissRainStartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, SENSOR_PRECIPITATION)

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.precipitation

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        data = self.coordinator.data
        ctx = (data.forecast_context if data else None) or {}
        return {
            "now_label": ctx.get("now_label"),
            "intensity_series": list(data.intensity_series) if data else [],
        }


class NearestRainSensor(RainStartEntity, SensorEntity):
    """Distance to the nearest wet blob when the home cell is dry."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:radar"

    def __init__(self, coordinator: MeteoSwissRainStartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, SENSOR_NEAREST_RAIN)

    @property
    def native_value(self) -> float | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.nearest_km


class RainEndSensor(RainStartEntity, SensorEntity):
    """Minutes until the current or next wet stretch goes dry."""

    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:weather-partly-cloudy"

    def __init__(self, coordinator: MeteoSwissRainStartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, SENSOR_RAIN_END)

    @property
    def native_value(self) -> int | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.minutes_until_dry

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        data = self.coordinator.data
        return {
            "rain_end": data.rain_end.isoformat() if data and data.rain_end else None,
        }


class DataAgeSensor(RainStartEntity, SensorEntity):
    """Minutes since the latest radar measurement frame."""

    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator: MeteoSwissRainStartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, SENSOR_DATA_AGE)

    @property
    def native_value(self) -> int | None:
        data = self.coordinator.data
        if not data:
            return None
        return data_age_minutes(data.source_updated, datetime.now().astimezone())

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        data = self.coordinator.data
        return {
            "source_updated": data.source_updated.isoformat() if data else None,
        }


class NextFetchSensor(RainStartEntity, SensorEntity):
    """When the coordinator will poll the radar again."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:update"

    def __init__(self, coordinator: MeteoSwissRainStartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, SENSOR_NEXT_FETCH)

    @property
    def native_value(self) -> datetime | None:
        last = self.coordinator.last_fetch_at
        interval = self.coordinator.update_interval
        if last is None or interval is None:
            return None
        return next_fetch_at(last, int(interval.total_seconds()))

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        interval = self.coordinator.update_interval
        last = self.coordinator.last_fetch_at
        return {
            "poll_interval_seconds": int(interval.total_seconds()) if interval else None,
            "last_fetch_at": last.isoformat() if last else None,
        }
