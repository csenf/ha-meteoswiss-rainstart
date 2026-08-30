"""Tests for frontend registration."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from meteoswiss_rainstart.const import DOMAIN
from meteoswiss_rainstart.frontend_register import async_register_frontend, card_module_url


def test_register_frontend_serves_card_once(tmp_path: Path) -> None:
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "rainstart-card.js").write_text("// card")

    hass = MagicMock()
    hass.data = {}
    hass.http.async_register_static_paths = AsyncMock()

    async def register_once() -> str:
        domain_data = hass.data.setdefault(DOMAIN, {})
        if domain_data.get("frontend_registered"):
            return str(domain_data["card_module_url"])
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(
                    f"/{DOMAIN}/frontend",
                    str(frontend),
                    cache_headers=False,
                )
            ]
        )
        module_url = card_module_url("0.2.0")
        domain_data["frontend_registered"] = True
        domain_data["card_module_url"] = module_url
        return module_url

    url1 = asyncio.run(register_once())
    url2 = asyncio.run(register_once())

    assert url1 == "/meteoswiss_rainstart/frontend/rainstart-card.js?v=0.2.0"
    assert url2 == url1
    hass.http.async_register_static_paths.assert_awaited_once()


def test_async_register_frontend_uses_integration_dir() -> None:
    hass = MagicMock()
    hass.data = {}
    hass.http.async_register_static_paths = AsyncMock()

    url = asyncio.run(async_register_frontend(hass, "1.2.3"))

    assert url == "/meteoswiss_rainstart/frontend/rainstart-card.js?v=1.2.3"
    assert hass.data[DOMAIN]["frontend_registered"] is True
    hass.http.async_register_static_paths.assert_awaited_once()
