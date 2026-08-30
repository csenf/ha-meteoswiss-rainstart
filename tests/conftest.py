"""Test harness: stub HA package so api tests run without homeassistant installed."""

from __future__ import annotations

import sys
import types
from pathlib import Path

_PKG_DIR = Path(__file__).resolve().parent.parent / "custom_components" / "meteoswiss_rainstart"
_PKG_NAME = "meteoswiss_rainstart"

if _PKG_NAME not in sys.modules:
    stub = types.ModuleType(_PKG_NAME)
    stub.__path__ = [str(_PKG_DIR)]
    sys.modules[_PKG_NAME] = stub


# --- Minimal stubs for homeassistant (used by location.py + config_flow helpers) ---
if "homeassistant" not in sys.modules:
    ha = types.ModuleType("homeassistant")
    sys.modules["homeassistant"] = ha

    # homeassistant.const
    ha_const = types.ModuleType("homeassistant.const")
    ha_const.CONF_LATITUDE = "latitude"
    ha_const.CONF_LONGITUDE = "longitude"

    class Platform:
        SENSOR = "sensor"
        BINARY_SENSOR = "binary_sensor"
        IMAGE = "image"

    ha_const.Platform = Platform
    ha_const.EVENT_HOMEASSISTANT_STARTED = "homeassistant_started"
    sys.modules["homeassistant.const"] = ha_const
    ha.const = ha_const

    # homeassistant.core
    ha_core = types.ModuleType("homeassistant.core")

    def _callback_decorator(func):
        return func

    ha_core.callback = _callback_decorator

    class HomeAssistant:
        """Minimal stub for type checking / construction in tests."""
        pass

    class CoreState:
        not_running = "not_running"
        starting = "starting"
        running = "running"
        stopping = "stopping"

    ha_core.HomeAssistant = HomeAssistant
    ha_core.CoreState = CoreState
    sys.modules["homeassistant.core"] = ha_core
    ha.core = ha_core

    # homeassistant.helpers
    ha_helpers = types.ModuleType("homeassistant.helpers")
    sys.modules["homeassistant.helpers"] = ha_helpers
    ha.helpers = ha_helpers

    # homeassistant.helpers.selector
    ha_selector = types.ModuleType("homeassistant.helpers.selector")

    class LocationSelectorConfig:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class LocationSelector:
        def __init__(self, config=None):
            self.config = config

    ha_selector.LocationSelector = LocationSelector
    ha_selector.LocationSelectorConfig = LocationSelectorConfig
    sys.modules["homeassistant.helpers.selector"] = ha_selector
    ha_helpers.selector = ha_selector

    # homeassistant.config_entries (minimal for type hints / isinstance in tests)
    ha_config_entries = types.ModuleType("homeassistant.config_entries")

    class ConfigEntry:
        pass

    class OptionsFlow:
        pass

    class ConfigFlow:
        """Stub base for config flow to allow subclassing."""
        def __init_subclass__(cls, domain=None, **kwargs):
            super().__init_subclass__(**kwargs)

    ha_config_entries.ConfigEntry = ConfigEntry
    ha_config_entries.OptionsFlow = OptionsFlow
    ha_config_entries.ConfigFlow = ConfigFlow
    sys.modules["homeassistant.config_entries"] = ha_config_entries
    ha.config_entries = ha_config_entries

    # homeassistant.data_entry_flow
    ha_data_entry = types.ModuleType("homeassistant.data_entry_flow")

    class FlowResult(dict):
        pass

    ha_data_entry.FlowResult = FlowResult
    sys.modules["homeassistant.data_entry_flow"] = ha_data_entry

    # homeassistant.exceptions
    ha_exceptions = types.ModuleType("homeassistant.exceptions")

    class HomeAssistantError(Exception):
        pass

    ha_exceptions.HomeAssistantError = HomeAssistantError
    sys.modules["homeassistant.exceptions"] = ha_exceptions



# --- Stub voluptuous (used by config_flow) ---
if "voluptuous" not in sys.modules:
    vol = types.ModuleType("voluptuous")

    class _Marker:
        def __init__(self, key, default=None, **kwargs):
            self.key = key
            self.default = default
            for k, v in kwargs.items():
                setattr(self, k, v)

        def __repr__(self):
            return f"Marker({self.key})"

        def __hash__(self):
            return hash(self.key)

        def __eq__(self, other):
            if isinstance(other, str):
                return self.key == other
            if isinstance(other, _Marker):
                return self.key == other.key
            return NotImplemented

    class Required(_Marker):
        pass

    class Optional(_Marker):
        pass

    class Schema(dict):
        def __init__(self, schema, **kwargs):
            super().__init__(schema)
            self.schema = schema

        def __call__(self, data):
            return data

    def All(*validators, **kwargs):
        return validators[0] if validators else (lambda x: x)

    def Range(**kwargs):
        def _range(v):
            return v
        return _range

    def Coerce(typ):
        def _coerce(v):
            return typ(v)
        return _coerce

    vol.Required = Required
    vol.Optional = Optional
    vol.Schema = Schema
    vol.All = All
    vol.Range = Range
    vol.Coerce = Coerce
    sys.modules["voluptuous"] = vol
    # also as 'vol' alias if used
    sys.modules["vol"] = vol


# Stubs needed when tests import coordinator / diagnostics helpers.
if "homeassistant.helpers.update_coordinator" not in sys.modules:
    ha_coord = types.ModuleType("homeassistant.helpers.update_coordinator")

    class UpdateFailed(Exception):
        pass

    class DataUpdateCoordinator:
        def __class_getitem__(cls, _item):
            return cls

        def __init__(self, hass, logger, name=None, update_interval=None, **kwargs):
            self.hass = hass
            self.logger = logger
            self.name = name
            self.update_interval = update_interval
            self.data = None

    ha_coord.UpdateFailed = UpdateFailed
    ha_coord.DataUpdateCoordinator = DataUpdateCoordinator
    sys.modules["homeassistant.helpers.update_coordinator"] = ha_coord
    sys.modules["homeassistant.helpers"].update_coordinator = ha_coord

if "homeassistant.helpers.translation" not in sys.modules:
    ha_trans = types.ModuleType("homeassistant.helpers.translation")

    async def async_get_translations(*_args, **_kwargs):
        return {}

    ha_trans.async_get_translations = async_get_translations
    sys.modules["homeassistant.helpers.translation"] = ha_trans
    sys.modules["homeassistant.helpers"].translation = ha_trans

if "homeassistant.components" not in sys.modules:
    ha_components = types.ModuleType("homeassistant.components")
    sys.modules["homeassistant.components"] = ha_components
    sys.modules["homeassistant"].components = ha_components

if "homeassistant.components.persistent_notification" not in sys.modules:
    ha_notify = types.ModuleType("homeassistant.components.persistent_notification")

    def async_create(*_args, **_kwargs):
        return None

    ha_notify.async_create = async_create
    sys.modules["homeassistant.components.persistent_notification"] = ha_notify
    sys.modules["homeassistant.components"].persistent_notification = ha_notify

if "homeassistant.components.diagnostics" not in sys.modules:
    ha_diag = types.ModuleType("homeassistant.components.diagnostics")

    def async_redact_data(data, keys):
        if isinstance(data, dict):
            return {
                key: "**REDACTED**" if key in keys else async_redact_data(value, keys)
                for key, value in data.items()
            }
        if isinstance(data, list):
            return [async_redact_data(item, keys) for item in data]
        return data

    ha_diag.async_redact_data = async_redact_data
    sys.modules["homeassistant.components.diagnostics"] = ha_diag
    sys.modules["homeassistant.components"].diagnostics = ha_diag

if "homeassistant.components.http" not in sys.modules:
    ha_http = types.ModuleType("homeassistant.components.http")

    class StaticPathConfig:
        def __init__(self, url_path, path, cache_headers=False):
            self.url_path = url_path
            self.path = path
            self.cache_headers = cache_headers

    ha_http.StaticPathConfig = StaticPathConfig
    sys.modules["homeassistant.components.http"] = ha_http
    sys.modules["homeassistant.components"].http = ha_http
