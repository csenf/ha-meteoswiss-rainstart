"""Serve the bundled Lovelace card and register it as a resource.

Serving the JS file over HTTP is not enough: Home Assistant's frontend
only loads a module if it is listed in Lovelace resources (Settings ->
Dashboards -> Resources, or ``lovelace: resources:`` in YAML mode). This
module adds the resource automatically in storage mode, which is the
default and covers most installs.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CARD_FILENAME = "rainstart-card.js"
URL_BASE = f"/{DOMAIN}/frontend"

DEFAULT_RETRY_SECONDS = 5
DEFAULT_MAX_ATTEMPTS = 12


def card_module_url(version: str) -> str:
    """Return the versioned module URL for the Lovelace card."""
    return f"{URL_BASE}/{CARD_FILENAME}?v={version}"


def plan_resource_action(existing_urls: list[str], target_url: str) -> str:
    """Decide whether a matching Lovelace resource needs create/update/noop.

    ``existing_urls`` are resource URLs already pointing at our card file
    (any ``?v=...`` suffix). Comparison ignores query string for matching
    but requires an exact match (including version) for "noop".
    """
    target_path = target_url.split("?", 1)[0]
    for url in existing_urls:
        if url.split("?", 1)[0] == target_path:
            return "noop" if url == target_url else "update"
    return "create"


async def _async_register_static_path(hass: HomeAssistant) -> None:
    """Serve the frontend directory; tolerate a repeat registration."""
    frontend_dir = Path(__file__).parent / "frontend"
    try:
        await hass.http.async_register_static_paths(
            [StaticPathConfig(URL_BASE, str(frontend_dir), cache_headers=False)]
        )
    except RuntimeError:
        _LOGGER.debug("Static path already registered: %s", URL_BASE)


async def _async_upsert_lovelace_resource(lovelace: Any, version: str) -> None:
    """Create or update the Lovelace resource entry for the card."""
    target_url = card_module_url(version)
    target_path = target_url.split("?", 1)[0]
    existing = [
        resource
        for resource in lovelace.resources.async_items()
        if resource.get("url", "").split("?", 1)[0] == target_path
    ]
    action = plan_resource_action([item["url"] for item in existing], target_url)
    if action == "create":
        await lovelace.resources.async_create_item(
            {"res_type": "module", "url": target_url}
        )
    elif action == "update":
        await lovelace.resources.async_update_item(
            existing[0]["id"], {"res_type": "module", "url": target_url}
        )


async def _async_wait_and_register_resource(
    hass: HomeAssistant,
    version: str,
    *,
    retry_seconds: float = DEFAULT_RETRY_SECONDS,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> bool:
    """Register the Lovelace resource once storage-mode resources are loaded.

    Returns False (without raising) when Lovelace is missing, in YAML
    mode, or never finishes loading within ``max_attempts`` — callers
    should treat that as "user must add the resource manually".
    """
    lovelace = hass.data.get("lovelace")
    if lovelace is None or getattr(lovelace, "mode", None) != "storage":
        return False

    for _ in range(max_attempts):
        if getattr(lovelace.resources, "loaded", True):
            await _async_upsert_lovelace_resource(lovelace, version)
            return True
        await asyncio.sleep(retry_seconds)

    _LOGGER.debug("Lovelace resources never finished loading; skipping auto-registration")
    return False


async def async_register_frontend(hass: HomeAssistant, version: str) -> None:
    """Serve the card once and add it to Lovelace resources when possible."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("frontend_registered"):
        return
    domain_data["frontend_registered"] = True

    await _async_register_static_path(hass)
    await _async_wait_and_register_resource(hass, version)
