"""Tests for scheduling the one-time frontend/resource registration.

Registration must happen from the component-level `async_setup`, once per
Home Assistant run, not from `async_setup_entry` (which runs per config
entry and may run before Lovelace resources are ready).

The `meteoswiss_rainstart` package is stubbed empty in conftest.py so
lightweight submodule tests avoid pulling in the full package `__init__`.
This test needs the real `__init__.py`, so it loads that file directly
under its own module name while pointing its relative imports (`.const`,
`.frontend_register`, ...) at the already-stubbed package.
"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.core import CoreState

_PKG_DIR = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "meteoswiss_rainstart"
)
_MODULE_NAME = "meteoswiss_rainstart._init_under_test"


def _load_init_module():
    if _MODULE_NAME in sys.modules:
        return sys.modules[_MODULE_NAME]
    spec = importlib.util.spec_from_file_location(_MODULE_NAME, _PKG_DIR / "__init__.py")
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "meteoswiss_rainstart"
    sys.modules[_MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


init_module = _load_init_module()


def test_setup_runs_registration_immediately_when_already_running() -> None:
    hass = MagicMock()
    hass.state = CoreState.running
    hass.data = {}
    scheduled = []
    hass.async_create_task = MagicMock(side_effect=lambda coro: scheduled.append(coro))

    with patch.object(init_module, "async_register_frontend", new=AsyncMock()):
        result = asyncio.run(init_module.async_setup(hass, {}))
        for coro in scheduled:
            asyncio.run(coro)

    assert result is True
    assert len(scheduled) == 1
    hass.bus.async_listen_once.assert_not_called()


def test_setup_waits_for_started_event_when_not_running() -> None:
    hass = MagicMock()
    hass.state = CoreState.not_running
    hass.data = {}

    with patch.object(init_module, "async_register_frontend", new=AsyncMock()):
        result = asyncio.run(init_module.async_setup(hass, {}))

    assert result is True
    hass.bus.async_listen_once.assert_called_once()
    event_name = hass.bus.async_listen_once.call_args.args[0]
    assert event_name == "homeassistant_started"
    hass.async_create_task.assert_not_called()
