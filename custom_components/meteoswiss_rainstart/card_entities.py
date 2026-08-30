"""Resolve Lovelace card entity ids from the primary next-rain sensor."""

from __future__ import annotations

from dataclasses import dataclass

from .const import (
    BINARY_PARSER_PROBLEM,
    BINARY_RAINING,
    DOMAIN,
    IMAGE_INTENSITY,
    SENSOR_DATA_AGE,
    SENSOR_KEY,
    SENSOR_NEAREST_RAIN,
    SENSOR_NEXT_FETCH,
    SENSOR_PRECIPITATION,
    SENSOR_RAIN_END,
)
from .location import slugify_location_name

CARD_ROLES = (
    "next_rain",
    "raining",
    "precipitation",
    "nearest_rain",
    "rain_end",
    "data_age",
    "next_fetch",
    "parser_problem",
    "intensity_graph",
)

_ROLE_KEYS: dict[str, tuple[str, str]] = {
    "next_rain": ("sensor", SENSOR_KEY),
    "precipitation": ("sensor", SENSOR_PRECIPITATION),
    "nearest_rain": ("sensor", SENSOR_NEAREST_RAIN),
    "rain_end": ("sensor", SENSOR_RAIN_END),
    "data_age": ("sensor", SENSOR_DATA_AGE),
    "next_fetch": ("sensor", SENSOR_NEXT_FETCH),
    "raining": ("binary_sensor", BINARY_RAINING),
    "parser_problem": ("binary_sensor", BINARY_PARSER_PROBLEM),
    "intensity_graph": ("image", IMAGE_INTENSITY),
}

_LEGACY_PRIMARY = f"sensor.{DOMAIN}_{SENSOR_KEY}"


@dataclass(frozen=True, slots=True)
class ParsedPrimary:
    """Primary next-rain entity id parsed from config."""

    slug: str | None
    legacy_primary: bool


def parse_next_rain_entity_id(entity_id: str) -> ParsedPrimary:
    """Parse a next-rain sensor entity id."""
    if entity_id == _LEGACY_PRIMARY:
        return ParsedPrimary(slug=None, legacy_primary=True)

    prefix = f"sensor.{DOMAIN}_"
    suffix = f"_{SENSOR_KEY}"
    if entity_id.startswith(prefix) and entity_id.endswith(suffix):
        slug = entity_id[len(prefix) : -len(suffix)]
        if slug:
            return ParsedPrimary(slug=slug, legacy_primary=False)

    raise ValueError("entity must be a MeteoSwiss Rain-Start next rain sensor")


def _entity_id(slug: str, platform: str, key: str) -> str:
    return f"{platform}.{DOMAIN}_{slug}_{key}"


def related_entity_ids(
    primary_entity_id: str,
    *,
    location_name: str | None = None,
) -> dict[str, str]:
    """Return related entity ids keyed by card role."""
    parsed = parse_next_rain_entity_id(primary_entity_id)
    if parsed.legacy_primary:
        if not location_name:
            raise ValueError("location_name is required for legacy next rain entity")
        slug = slugify_location_name(location_name)
    else:
        slug = parsed.slug or ""
        if not slug:
            raise ValueError("entity must include a location slug")

    related = {
        role: _entity_id(slug, platform, key) for role, (platform, key) in _ROLE_KEYS.items()
    }
    related["next_rain"] = primary_entity_id
    return related
