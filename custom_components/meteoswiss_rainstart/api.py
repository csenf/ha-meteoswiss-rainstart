"""Rain-start fetch: Switzerland bounds, LV95, website radar nowcast."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
from pyproj import Transformer

from .const import (
    CH_LAT_MAX,
    CH_LAT_MIN,
    CH_LON_MAX,
    CH_LON_MIN,
    DATA_SOURCE_RADAR,
    EPSG_LV95,
    EPSG_WGS84,
)

_LOGGER = logging.getLogger(__name__)
_WGS84_TO_LV95 = Transformer.from_crs(EPSG_WGS84, EPSG_LV95, always_xy=True)


class ApiError(Exception):
    """Base error for MeteoSwiss rain-start API."""


class DownloadError(ApiError):
    """Radar product download failed."""


class ParseError(ApiError):
    """Radar product parse failed."""


class OutOfBoundsError(ApiError):
    """Coordinates outside Switzerland."""


@dataclass(frozen=True, slots=True)
class RainStartResult:
    """Full rain-start payload returned to the coordinator."""

    minutes_until_rain: int | None
    rain_start: datetime | None
    intensity: float | None
    source_updated: datetime
    forecast_horizon_minutes: int
    data_source: str = DATA_SOURCE_RADAR
    forecast_context: dict[str, str | int | float | None] | None = None
    raining: bool = False
    precipitation: float = 0.0
    nearest_km: float | None = None
    minutes_until_dry: int | None = None
    rain_end: datetime | None = None
    intensity_series: tuple[dict[str, Any], ...] = ()


def is_within_switzerland(lat: float, lon: float) -> bool:
    """Return True when coordinates lie inside the published CH extent."""
    return CH_LAT_MIN <= lat <= CH_LAT_MAX and CH_LON_MIN <= lon <= CH_LON_MAX


def lat_lon_to_lv95(lat: float, lon: float) -> tuple[float, float]:
    """Convert WGS84 lat/lon to Swiss LV95 east/north metres."""
    east, north = _WGS84_TO_LV95.transform(lon, lat)
    return float(east), float(north)


def fetch_rain_start(
    lat: float,
    lon: float,
    threshold: float,
    *,
    http_client: httpx.Client | None = None,
) -> RainStartResult:
    """Fetch rain-start from the website radar nowcast."""
    if not is_within_switzerland(lat, lon):
        raise OutOfBoundsError(f"Coordinates ({lat}, {lon}) outside Switzerland")

    from .radar_nowcast import fetch_rain_start_radar

    result = fetch_rain_start_radar(
        lat,
        lon,
        threshold,
        http_client=http_client,
    )
    _LOGGER.debug("Rain-start from website radar nowcast")
    return result
