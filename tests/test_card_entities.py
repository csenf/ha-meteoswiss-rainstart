"""Tests for Lovelace card entity resolution."""

import pytest

from meteoswiss_rainstart.card_entities import (
    CARD_ROLES,
    parse_next_rain_entity_id,
    related_entity_ids,
)


def test_parse_slugged_next_rain_entity() -> None:
    parsed = parse_next_rain_entity_id(
        "sensor.meteoswiss_rainstart_belp_next_rain_minutes"
    )
    assert parsed.slug == "belp"


def test_parse_rejects_unrelated_entity() -> None:
    with pytest.raises(ValueError, match="next rain"):
        parse_next_rain_entity_id("sensor.meteoswiss_rainstart_belp_precipitation")


def test_related_entity_ids_for_named_location() -> None:
    ids = related_entity_ids("sensor.meteoswiss_rainstart_belp_next_rain_minutes")
    assert ids["next_rain"] == "sensor.meteoswiss_rainstart_belp_next_rain_minutes"
    assert ids["raining"] == "binary_sensor.meteoswiss_rainstart_belp_raining"
    assert ids["precipitation"] == "sensor.meteoswiss_rainstart_belp_precipitation"
    assert ids["nearest_rain"] == "sensor.meteoswiss_rainstart_belp_nearest_rain"
    assert ids["rain_end"] == "sensor.meteoswiss_rainstart_belp_rain_end_minutes"
    assert ids["data_age"] == "sensor.meteoswiss_rainstart_belp_data_age_minutes"
    assert ids["next_fetch"] == "sensor.meteoswiss_rainstart_belp_next_fetch"
    assert ids["parser_problem"] == (
        "binary_sensor.meteoswiss_rainstart_belp_parser_problem"
    )
    assert ids["intensity_graph"] == (
        "image.meteoswiss_rainstart_belp_intensity_graph"
    )


def test_card_roles_cover_all_related_keys() -> None:
    sample = related_entity_ids("sensor.meteoswiss_rainstart_belp_next_rain_minutes")
    assert set(sample) == set(CARD_ROLES)
