"""Config flow for MeteoSwiss Rain-Start."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .api import is_within_switzerland
from .const import (
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LOCATION_NAME,
    CONF_LONGITUDE,
    CONF_POLL_INTERVAL,
    CONF_THRESHOLD,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_THRESHOLD_MM,
    DOMAIN,
    MAX_POLL_INTERVAL,
    MAX_THRESHOLD_MM,
    MIN_POLL_INTERVAL,
    MIN_THRESHOLD_MM,
)
from .location import (
    normalize_location_name,
    parse_location_from_input,
    unique_id_for_coordinates,
    unique_id_in_use,
)


@dataclass(frozen=True, slots=True)
class SetupInput:
    """Validated setup or options values."""

    latitude: float
    longitude: float
    location_name: str
    threshold: float
    poll_interval: int


def build_setup_schema() -> vol.Schema:
    """Shared schema for user and options steps."""
    return vol.Schema(
        {
            vol.Required(CONF_LOCATION): selector.LocationSelector(
                selector.LocationSelectorConfig(
                    radius=False,
                    icon="mdi:weather-pouring",
                )
            ),
            vol.Required(CONF_LOCATION_NAME): str,
            vol.Optional(CONF_THRESHOLD, default=DEFAULT_THRESHOLD_MM): vol.All(
                vol.Coerce(float),
                vol.Range(min=MIN_THRESHOLD_MM, max=MAX_THRESHOLD_MM),
            ),
            vol.Optional(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): vol.All(
                vol.Coerce(int),
                vol.Range(min=MIN_POLL_INTERVAL, max=MAX_POLL_INTERVAL),
            ),
        }
    )


def parse_setup_input(user_input: dict[str, Any]) -> tuple[SetupInput | None, dict[str, str]]:
    """Validate map pin, name, threshold, and poll interval."""
    errors: dict[str, str] = {}
    latitude = 0.0
    longitude = 0.0
    try:
        latitude, longitude = parse_location_from_input(user_input.get(CONF_LOCATION))
    except ValueError:
        errors["base"] = "invalid_location"
    else:
        if not is_within_switzerland(latitude, longitude):
            errors["base"] = "outside_switzerland"

    try:
        location_name = normalize_location_name(user_input.get(CONF_LOCATION_NAME))
    except ValueError:
        errors[CONF_LOCATION_NAME] = "name_required"
        location_name = ""

    try:
        threshold = float(user_input[CONF_THRESHOLD])
        if not MIN_THRESHOLD_MM <= threshold <= MAX_THRESHOLD_MM:
            errors[CONF_THRESHOLD] = "threshold_invalid"
    except (KeyError, TypeError, ValueError):
        errors[CONF_THRESHOLD] = "threshold_invalid"
        threshold = DEFAULT_THRESHOLD_MM

    try:
        poll_interval = int(user_input[CONF_POLL_INTERVAL])
        if not MIN_POLL_INTERVAL <= poll_interval <= MAX_POLL_INTERVAL:
            errors[CONF_POLL_INTERVAL] = "poll_interval_invalid"
    except (KeyError, TypeError, ValueError):
        errors[CONF_POLL_INTERVAL] = "poll_interval_invalid"
        poll_interval = DEFAULT_POLL_INTERVAL

    if errors:
        return None, errors
    return SetupInput(
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        threshold=threshold,
        poll_interval=poll_interval,
    ), {}


def _entry_data(parsed: SetupInput) -> dict[str, float | int | str]:
    return {
        CONF_LATITUDE: parsed.latitude,
        CONF_LONGITUDE: parsed.longitude,
        CONF_LOCATION_NAME: parsed.location_name,
        CONF_THRESHOLD: parsed.threshold,
        CONF_POLL_INTERVAL: parsed.poll_interval,
    }


class MeteoSwissRainStartConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MeteoSwiss Rain-Start."""

    VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> MeteoSwissRainStartOptionsFlow:
        return MeteoSwissRainStartOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=self._default_schema(),
            )

        parsed, errors = parse_setup_input(user_input)
        if parsed is None:
            return self.async_show_form(
                step_id="user",
                data_schema=self.add_suggested_values_to_schema(
                    build_setup_schema(), user_input
                ),
                errors=errors,
            )

        await self.async_set_unique_id(
            unique_id_for_coordinates(parsed.latitude, parsed.longitude)
        )
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=parsed.location_name,
            data=_entry_data(parsed),
        )

    @callback
    def _default_schema(self) -> vol.Schema:
        """Build schema with Home Assistant defaults."""
        return self.add_suggested_values_to_schema(
            build_setup_schema(),
            {
                CONF_LOCATION: {
                    CONF_LATITUDE: self.hass.config.latitude,
                    CONF_LONGITUDE: self.hass.config.longitude,
                },
                CONF_THRESHOLD: DEFAULT_THRESHOLD_MM,
                CONF_POLL_INTERVAL: DEFAULT_POLL_INTERVAL,
            },
        )


class MeteoSwissRainStartOptionsFlow(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors: dict[str, str] = {}
        entry = self.config_entry

        if user_input is None:
            return self.async_show_form(
                step_id="init",
                data_schema=self._options_schema(entry),
            )

        parsed, errors = parse_setup_input(user_input)
        if parsed is not None:
            new_unique_id = unique_id_for_coordinates(
                parsed.latitude, parsed.longitude
            )
            if unique_id_in_use(
                self.hass.config_entries.async_entries(DOMAIN),
                new_unique_id,
                entry.entry_id,
            ):
                errors["base"] = "already_configured"
            else:
                self.hass.config_entries.async_update_entry(
                    entry,
                    data=_entry_data(parsed),
                    title=parsed.location_name,
                    unique_id=new_unique_id,
                )
                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                build_setup_schema(), user_input
            ),
            errors=errors,
        )

    @callback
    def _options_schema(self, entry):
        return self.add_suggested_values_to_schema(
            build_setup_schema(),
            {
                CONF_LOCATION: {
                    CONF_LATITUDE: entry.data[CONF_LATITUDE],
                    CONF_LONGITUDE: entry.data[CONF_LONGITUDE],
                },
                CONF_LOCATION_NAME: entry.data.get(CONF_LOCATION_NAME, ""),
                CONF_THRESHOLD: entry.data.get(CONF_THRESHOLD, DEFAULT_THRESHOLD_MM),
                CONF_POLL_INTERVAL: entry.data.get(
                    CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL
                ),
            },
        )
