"""Location naming helpers for config and entity registry."""

from __future__ import annotations

import re
import unicodedata

from .const import CONF_LATITUDE, CONF_LOCATION_NAME, CONF_LONGITUDE, DOMAIN, SENSOR_KEY

_SLUG_RE = re.compile(r"[^a-z0-9]+")

_UMlAUT_MAP = str.maketrans({
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
})


def slugify_location_name(name: str) -> str:
    """Normalize a display name to a safe entity_id slug."""
    # Transliterate German umlauts before NFKD to satisfy expected "bueren"
    name = name.translate(_UMlAUT_MAP)
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = _SLUG_RE.sub("_", ascii_name.lower()).strip("_")
    return slug or "location"


def format_coordinate_label(latitude: float, longitude: float) -> str:
    """Human-readable coordinate fallback (v1 migration only)."""
    return f"{latitude:.2f}, {longitude:.2f}"


def parse_location_from_input(location: object) -> tuple[float, float]:
    """Extract lat/lon from a LocationSelector dict."""
    if not isinstance(location, dict):
        raise ValueError("location is required")
    try:
        return float(location[CONF_LATITUDE]), float(location[CONF_LONGITUDE])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("location is required") from exc


def unique_id_for_coordinates(latitude: float, longitude: float) -> str:
    """Stable config-entry unique id for a pin (4 decimal degrees)."""
    return f"{latitude:.4f}_{longitude:.4f}"


def unique_id_in_use(
    entries: list[object], unique_id: str, skip_entry_id: str
) -> bool:
    """Return True when another config entry already owns unique_id."""
    return any(
        getattr(entry, "unique_id", None) == unique_id
        and getattr(entry, "entry_id", None) != skip_entry_id
        for entry in entries
    )


def normalize_location_name(user_name: str | None) -> str:
    """Strip a required user-entered location name."""
    if user_name is None or not (stripped := user_name.strip()):
        raise ValueError("location name is required")
    return stripped


def entity_id_for(location_name: str, key: str, platform: str = "sensor") -> str:
    slug = slugify_location_name(location_name)
    return f"{platform}.{DOMAIN}_{slug}_{key}"


def entity_id_for_location(location_name: str) -> str:
    return entity_id_for(location_name, SENSOR_KEY)


def assigned_entity_id(entry_data: dict, key: str, platform: str) -> str | None:
    """Entity id for a new entity, or None to let Home Assistant assign one."""
    if key == SENSOR_KEY and entry_data.get("_legacy_entity_id"):
        return f"sensor.{DOMAIN}_{SENSOR_KEY}"
    name = entry_data.get(CONF_LOCATION_NAME)
    if name:
        return entity_id_for(name, key, platform)
    return None


def migrate_v1_data(data: dict) -> tuple[dict, str]:
    """Add location_name and the legacy entity-id flag to a v1 entry."""
    updated = dict(data)
    if CONF_LOCATION_NAME not in updated:
        name = format_coordinate_label(updated[CONF_LATITUDE], updated[CONF_LONGITUDE])
        updated[CONF_LOCATION_NAME] = name
        updated["_legacy_entity_id"] = True
        return updated, name
    return updated, str(updated[CONF_LOCATION_NAME])
