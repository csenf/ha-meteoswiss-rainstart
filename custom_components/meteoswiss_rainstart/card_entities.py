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

@dataclass(frozen=True, slots=True)
class ParsedPrimary:
    """Primary next-rain entity id parsed from config."""

    slug: str


def parse_next_rain_entity_id(entity_id: str) -> ParsedPrimary:
    """Parse a next-rain sensor entity id."""
    prefix = f"sensor.{DOMAIN}_"
    suffix = f"_{SENSOR_KEY}"
    if entity_id.startswith(prefix) and entity_id.endswith(suffix):
        slug = entity_id[len(prefix) : -len(suffix)]
        if slug:
            return ParsedPrimary(slug=slug)

    raise ValueError("entity must be a MeteoSwiss Rain-Start next rain sensor")


def _entity_id(slug: str, platform: str, key: str) -> str:
    return f"{platform}.{DOMAIN}_{slug}_{key}"


def related_entity_ids(primary_entity_id: str) -> dict[str, str]:
    """Return related entity ids keyed by card role."""
    parsed = parse_next_rain_entity_id(primary_entity_id)
    related = {
        role: _entity_id(parsed.slug, platform, key)
        for role, (platform, key) in _ROLE_KEYS.items()
    }
    related["next_rain"] = primary_entity_id
    return related
