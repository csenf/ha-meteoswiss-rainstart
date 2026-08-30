"""Register bundled Lovelace card static assets."""

from __future__ import annotations

from pathlib import Path

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant

from .const import DOMAIN


def card_module_url(version: str) -> str:
    """Return the versioned module URL for the Lovelace card."""
    return f"/{DOMAIN}/frontend/rainstart-card.js?v={version}"


async def async_register_frontend(hass: HomeAssistant, version: str) -> str:
    """Serve frontend assets once and return the card module URL."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("frontend_registered"):
        return str(domain_data["card_module_url"])

    frontend_dir = Path(__file__).parent / "frontend"
    url_prefix = f"/{DOMAIN}/frontend"
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                url_prefix,
                str(frontend_dir),
                cache_headers=False,
            )
        ]
    )
    module_url = card_module_url(version)
    domain_data["frontend_registered"] = True
    domain_data["card_module_url"] = module_url
    return module_url
