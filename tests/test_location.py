"""Tests for location naming helpers."""

import pytest

from meteoswiss_rainstart.const import CONF_LOCATION, CONF_LOCATION_NAME
from meteoswiss_rainstart.location import (
    assigned_entity_id,
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


def test_assigned_entity_id_from_location_name():
    assert assigned_entity_id(
        {"location_name": "Belp"}, "precipitation", "sensor"
    ) == "sensor.meteoswiss_rainstart_belp_precipitation"
    assert assigned_entity_id({}, "precipitation", "sensor") is None


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
