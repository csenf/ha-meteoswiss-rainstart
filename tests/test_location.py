"""Tests for location naming helpers."""

import pytest

from meteoswiss_rainstart.const import CONF_LOCATION, CONF_LOCATION_NAME
from meteoswiss_rainstart.location import (
    assigned_entity_id,
    format_coordinate_label,
    migrate_v1_data,
    normalize_location_name,
    parse_location_from_input,
    slugify_location_name,
    unique_id_for_coordinates,
    unique_id_in_use,
)


def test_slugify_simple():
    assert slugify_location_name("Belp") == "belp"


def test_slugify_umlaut():
    assert slugify_location_name("Büren") == "bueren"


def test_slugify_spaces_and_punctuation():
    assert slugify_location_name("Garden Shed!") == "garden_shed"


def test_format_coordinate_label():
    assert format_coordinate_label(46.8912, 7.5023) == "46.89, 7.50"


def test_conf_keys_exist():
    assert CONF_LOCATION == "location"
    assert CONF_LOCATION_NAME == "location_name"


def test_normalize_strips_user_name():
    assert normalize_location_name("  Belp  ") == "Belp"


def test_normalize_rejects_empty():
    with pytest.raises(ValueError, match="location name is required"):
        normalize_location_name(None)
    with pytest.raises(ValueError, match="location name is required"):
        normalize_location_name("")
    with pytest.raises(ValueError, match="location name is required"):
        normalize_location_name("   ")


def test_parse_location_rejects_bad_input():
    with pytest.raises(ValueError, match="location is required"):
        parse_location_from_input(None)
    with pytest.raises(ValueError, match="location is required"):
        parse_location_from_input({"latitude": "x", "longitude": 7.5})
    with pytest.raises(ValueError, match="location is required"):
        parse_location_from_input({"latitude": 46.9})


def test_unique_id_and_conflict():
    uid = unique_id_for_coordinates(46.8986, 7.49578)
    assert uid == "46.8986_7.4958"

    class Entry:
        def __init__(self, entry_id, unique_id):
            self.entry_id = entry_id
            self.unique_id = unique_id

    entries = [Entry("a", uid), Entry("b", "other")]
    assert unique_id_in_use(entries, uid, "a") is False
    assert unique_id_in_use(entries, uid, "b") is True


def test_assigned_entity_id_legacy_and_named():
    assert assigned_entity_id({"_legacy_entity_id": True}, "next_rain_minutes", "sensor") == (
        "sensor.meteoswiss_rainstart_next_rain_minutes"
    )
    assert assigned_entity_id(
        {"location_name": "Belp"}, "precipitation", "sensor"
    ) == "sensor.meteoswiss_rainstart_belp_precipitation"
    assert assigned_entity_id({}, "precipitation", "sensor") is None


def test_migrate_v1_data_adds_name_and_legacy_flag():
    data, title = migrate_v1_data({"latitude": 46.8912, "longitude": 7.5023})
    assert title == "46.89, 7.50"
    assert data["location_name"] == title
    assert data["_legacy_entity_id"] is True


def test_migrate_v1_data_keeps_existing_name():
    data, title = migrate_v1_data(
        {"latitude": 46.89, "longitude": 7.50, "location_name": "Belp"}
    )
    assert title == "Belp"
    assert "_legacy_entity_id" not in data


def test_entity_id_slug_from_name():
    from meteoswiss_rainstart.location import entity_id_for, entity_id_for_location

    assert entity_id_for_location("Belp") == "sensor.meteoswiss_rainstart_belp_next_rain_minutes"
    assert entity_id_for("Belp", "precipitation") == (
        "sensor.meteoswiss_rainstart_belp_precipitation"
    )
    assert entity_id_for("Belp", "raining", platform="binary_sensor") == (
        "binary_sensor.meteoswiss_rainstart_belp_raining"
    )
    assert entity_id_for("Belp", "intensity_graph", platform="image") == (
        "image.meteoswiss_rainstart_belp_intensity_graph"
    )
