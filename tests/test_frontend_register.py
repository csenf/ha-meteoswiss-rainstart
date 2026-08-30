"""Tests for bundled Lovelace card registration.

The card previously only served a static JS file. Home Assistant's
frontend never loads a JS module unless it is also registered as a
Lovelace resource, so the card silently failed to "arrive" for anyone
who did not add it by hand under Settings -> Dashboards -> Resources.

These tests cover the fix: auto-register (and auto-update) the resource
in storage-mode Lovelace, and fail closed (no crash) otherwise.

The Lovelace stub mirrors ``homeassistant.components.lovelace.LovelaceData``
and ``ResourceStorageCollection`` field/method names exactly (checked
against Home Assistant core source), because a mismatched attribute name
here previously made the auto-registration silently never fire.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from meteoswiss_rainstart.const import DOMAIN
from meteoswiss_rainstart.frontend_register import (
    _async_register_resource,
    _async_register_static_path,
    _async_upsert_lovelace_resource,
    async_register_frontend,
    card_module_url,
    plan_resource_action,
)


def test_card_module_url_includes_cache_busting_version() -> None:
    assert card_module_url("0.3.0") == (
        "/meteoswiss_rainstart/frontend/rainstart-card.js?v=0.3.0"
    )


def test_plan_resource_action_creates_when_absent() -> None:
    assert plan_resource_action([], "url.js?v=1") == "create"


def test_plan_resource_action_updates_on_version_change() -> None:
    assert plan_resource_action(["url.js?v=1"], "url.js?v=2") == "update"


def test_plan_resource_action_noop_when_current() -> None:
    assert plan_resource_action(["url.js?v=2"], "url.js?v=2") == "noop"


def _lovelace_stub(resource_mode="storage", existing_resources=None):
    lovelace = MagicMock()
    lovelace.resource_mode = resource_mode
    lovelace.resources.async_get_info = AsyncMock(return_value={"resources": 0})
    lovelace.resources.async_items = MagicMock(return_value=list(existing_resources or []))
    lovelace.resources.async_create_item = AsyncMock()
    lovelace.resources.async_update_item = AsyncMock()
    return lovelace


def test_upsert_creates_resource_when_missing() -> None:
    lovelace = _lovelace_stub(existing_resources=[])

    asyncio.run(_async_upsert_lovelace_resource(lovelace, "0.3.0"))

    lovelace.resources.async_create_item.assert_awaited_once_with(
        {
            "res_type": "module",
            "url": "/meteoswiss_rainstart/frontend/rainstart-card.js?v=0.3.0",
        }
    )
    lovelace.resources.async_update_item.assert_not_awaited()


def test_upsert_updates_resource_on_version_bump() -> None:
    lovelace = _lovelace_stub(
        existing_resources=[
            {
                "id": "abc123",
                "url": "/meteoswiss_rainstart/frontend/rainstart-card.js?v=0.2.0",
            }
        ]
    )

    asyncio.run(_async_upsert_lovelace_resource(lovelace, "0.3.0"))

    lovelace.resources.async_update_item.assert_awaited_once_with(
        "abc123",
        {
            "res_type": "module",
            "url": "/meteoswiss_rainstart/frontend/rainstart-card.js?v=0.3.0",
        },
    )
    lovelace.resources.async_create_item.assert_not_awaited()


def test_upsert_noop_when_already_current() -> None:
    lovelace = _lovelace_stub(
        existing_resources=[
            {
                "id": "abc123",
                "url": "/meteoswiss_rainstart/frontend/rainstart-card.js?v=0.3.0",
            }
        ]
    )

    asyncio.run(_async_upsert_lovelace_resource(lovelace, "0.3.0"))

    lovelace.resources.async_create_item.assert_not_awaited()
    lovelace.resources.async_update_item.assert_not_awaited()


def test_register_resource_skips_yaml_mode() -> None:
    hass = MagicMock()
    lovelace = _lovelace_stub(resource_mode="yaml")
    hass.data = {"lovelace": lovelace}

    registered = asyncio.run(_async_register_resource(hass, "0.3.0"))

    assert registered is False
    lovelace.resources.async_create_item.assert_not_awaited()


def test_register_resource_skips_when_lovelace_missing() -> None:
    hass = MagicMock()
    hass.data = {}

    registered = asyncio.run(_async_register_resource(hass, "0.3.0"))

    assert registered is False


def test_register_resource_ensures_collection_loaded_before_registering() -> None:
    """Real ResourceStorageCollection.async_items() only reflects storage state
    after loading. We must await async_get_info() (which ensures loading)
    before inspecting existing items, not just fire-and-forget.
    """
    hass = MagicMock()
    lovelace = _lovelace_stub(resource_mode="storage", existing_resources=[])
    hass.data = {"lovelace": lovelace}

    registered = asyncio.run(_async_register_resource(hass, "0.3.0"))

    assert registered is True
    lovelace.resources.async_get_info.assert_awaited_once()
    lovelace.resources.async_create_item.assert_awaited_once()


def test_register_static_path_is_idempotent_on_runtime_error() -> None:
    hass = MagicMock()
    hass.http.async_register_static_paths = AsyncMock(side_effect=RuntimeError("dup"))

    asyncio.run(_async_register_static_path(hass))  # must not raise

    hass.http.async_register_static_paths.assert_awaited_once()


def test_async_register_frontend_serves_and_registers_resource_once(tmp_path: Path) -> None:
    hass = MagicMock()
    hass.data = {}
    hass.http.async_register_static_paths = AsyncMock()
    lovelace = _lovelace_stub(existing_resources=[])
    hass.data["lovelace"] = lovelace

    asyncio.run(async_register_frontend(hass, "0.3.0"))
    asyncio.run(async_register_frontend(hass, "0.3.0"))

    hass.http.async_register_static_paths.assert_awaited_once()
    lovelace.resources.async_create_item.assert_awaited_once()
    assert hass.data[DOMAIN]["frontend_registered"] is True


def test_async_register_frontend_does_not_crash_without_lovelace() -> None:
    hass = MagicMock()
    hass.data = {}
    hass.http.async_register_static_paths = AsyncMock()

    asyncio.run(async_register_frontend(hass, "0.3.0"))  # must not raise

    hass.http.async_register_static_paths.assert_awaited_once()
