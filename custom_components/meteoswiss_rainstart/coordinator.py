"""DataUpdateCoordinator for MeteoSwiss Rain-Start."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import translation
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    DownloadError,
    OutOfBoundsError,
    ParseError,
    RainStartResult,
    fetch_rain_start,
    is_within_switzerland,
)
from .const import (
    CONF_LATITUDE,
    CONF_LOCATION_NAME,
    CONF_LONGITUDE,
    CONF_POLL_INTERVAL,
    CONF_THRESHOLD,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_THRESHOLD_MM,
    DOMAIN,
    FETCH_STATUS_DOWNLOAD_ERROR,
    FETCH_STATUS_ERROR,
    FETCH_STATUS_OK,
    FETCH_STATUS_OUT_OF_BOUNDS,
    FETCH_STATUS_PARSE_ERROR,
)

_LOGGER = logging.getLogger(__name__)


def classify_update_error(exc: BaseException) -> tuple[str, bool]:
    """Map a fetch exception to (last_fetch_status, is_parse_problem)."""
    if isinstance(exc, OutOfBoundsError):
        return FETCH_STATUS_OUT_OF_BOUNDS, False
    if isinstance(exc, DownloadError):
        return FETCH_STATUS_DOWNLOAD_ERROR, False
    if isinstance(exc, ParseError):
        return FETCH_STATUS_PARSE_ERROR, True
    return FETCH_STATUS_ERROR, False


class MeteoSwissRainStartCoordinator(DataUpdateCoordinator[RainStartResult]):
    """Fetch rain-start estimates from the website radar nowcast."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.latitude = float(entry.data[CONF_LATITUDE])
        self.longitude = float(entry.data[CONF_LONGITUDE])
        self.threshold = float(entry.data.get(CONF_THRESHOLD, DEFAULT_THRESHOLD_MM))
        poll_interval = int(entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL))

        self.last_fetch_status = FETCH_STATUS_OK
        self.last_fetch_at: datetime | None = None
        self.data_source: str | None = None
        self.parse_ok = True
        self.parse_detail = "pending"

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=poll_interval),
        )

    async def _async_setup(self) -> None:
        """Validate coordinates before the first poll."""
        if not is_within_switzerland(self.latitude, self.longitude):
            self.last_fetch_status = FETCH_STATUS_OUT_OF_BOUNDS
            _LOGGER.warning(
                "Location (%.4f, %.4f) is outside Switzerland radar coverage",
                self.latitude,
                self.longitude,
            )
            raise UpdateFailed("Location outside Switzerland radar coverage")

    async def _async_update_data(self) -> RainStartResult:
        """Poll the website radar nowcast."""
        self.last_fetch_at = datetime.now().astimezone()
        try:
            result = await self.hass.async_add_executor_job(
                fetch_rain_start,
                self.latitude,
                self.longitude,
                self.threshold,
            )
        except Exception as exc:
            status, is_parse = classify_update_error(exc)
            self.last_fetch_status = status
            if is_parse:
                await self._async_mark_parse_problem(str(exc))
            raise UpdateFailed(str(exc)) from exc

        self.last_fetch_status = FETCH_STATUS_OK
        self.parse_ok = True
        self.parse_detail = "ok"
        self.data_source = result.data_source
        return result

    async def _async_mark_parse_problem(self, detail: str) -> None:
        """Record a parser failure and notify once when health drops."""
        was_ok = self.parse_ok
        self.parse_ok = False
        self.parse_detail = detail
        if was_ok:
            await self._async_notify_parser_problem(detail)

    async def _async_notify_parser_problem(self, detail: str) -> None:
        """Notify once when the unofficial radar JSON no longer parses."""
        location_name = self.entry.data.get(CONF_LOCATION_NAME, DOMAIN)
        strings = await translation.async_get_translations(
            self.hass,
            self.hass.config.language,
            "common",
            {DOMAIN},
        )
        title = strings.get(
            f"component.{DOMAIN}.parser_problem.title",
            "MeteoSwiss Rain-Start: radar parse failed",
        )
        message = strings.get(
            f"component.{DOMAIN}.parser_problem.message",
            (
                "Rain-start for {location_name} can no longer parse the MeteoSwiss "
                "radar nowcast ({detail}). Other sensors are unavailable until the "
                "feed matches again."
            ),
        ).format(location_name=location_name, detail=detail)

        persistent_notification.async_create(
            self.hass,
            message=message,
            title=title,
            notification_id=f"{DOMAIN}.{self.entry.entry_id}.parser_problem",
        )

    @property
    def diagnostics_snapshot(self) -> dict[str, Any]:
        """Return read-only diagnostics data."""
        return {
            "data_source": self.data_source,
            "last_fetch_status": self.last_fetch_status,
            "parse_ok": self.parse_ok,
            "parse_detail": self.parse_detail,
            "last_fetch_at": self.last_fetch_at.isoformat()
            if self.last_fetch_at
            else None,
            "configured_threshold_mm": self.threshold,
            "location_name": self.entry.data.get(CONF_LOCATION_NAME),
            "configured_location": {
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
        }
