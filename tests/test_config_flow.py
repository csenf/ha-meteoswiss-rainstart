"""Config flow helper tests (no HA instance)."""

from types import SimpleNamespace

from meteoswiss_rainstart.config_flow import (
    MeteoSwissRainStartConfigFlow,
    build_setup_schema,
    parse_setup_input,
)
from meteoswiss_rainstart.const import (
    CONF_LOCATION,
    CONF_LOCATION_NAME,
    CONF_POLL_INTERVAL,
    CONF_THRESHOLD,
)


def _schema_key(schema, name: str):
    for key in schema.schema:
        if getattr(key, "key", key) == name:
            return key
    raise AssertionError(f"{name} not in schema")


def _valid_input(**overrides):
    data = {
        CONF_LOCATION: {"latitude": 46.8986, "longitude": 7.49578},
        CONF_LOCATION_NAME: "Belp",
        CONF_THRESHOLD: 0.2,
        CONF_POLL_INTERVAL: 300,
    }
    data.update(overrides)
    return data


def test_build_setup_schema_has_location_selector():
    schema = build_setup_schema()
    assert CONF_LOCATION in schema.schema
    assert CONF_THRESHOLD in schema.schema


def test_build_setup_schema_requires_location_name():
    schema = build_setup_schema()
    name_key = _schema_key(schema, CONF_LOCATION_NAME)
    assert type(name_key).__name__ == "Required"


def test_parse_setup_input_accepts_belp():
    parsed, errors = parse_setup_input(_valid_input())
    assert errors == {}
    assert parsed is not None
    assert parsed.location_name == "Belp"
    assert parsed.latitude == 46.8986


def test_parse_setup_input_rejects_outside_switzerland():
    parsed, errors = parse_setup_input(
        _valid_input(location={"latitude": 52.52, "longitude": 13.405})
    )
    assert parsed is None
    assert errors["base"] == "outside_switzerland"


def test_parse_setup_input_rejects_bad_location_and_name():
    parsed, errors = parse_setup_input(
        {
            CONF_LOCATION: None,
            CONF_LOCATION_NAME: "  ",
            CONF_THRESHOLD: 0.1,
            CONF_POLL_INTERVAL: 300,
        }
    )
    assert parsed is None
    assert errors["base"] == "invalid_location"
    assert errors[CONF_LOCATION_NAME] == "name_required"


def test_parse_setup_input_rejects_threshold_and_poll_range():
    parsed, errors = parse_setup_input(
        _valid_input(**{CONF_THRESHOLD: -1, CONF_POLL_INTERVAL: 10})
    )
    assert parsed is None
    assert errors[CONF_THRESHOLD] == "threshold_invalid"
    assert errors[CONF_POLL_INTERVAL] == "poll_interval_invalid"


def test_options_flow_is_registered_on_config_flow():
    handler = MeteoSwissRainStartConfigFlow.async_get_options_flow
    entry = SimpleNamespace(entry_id="e1", data={})
    flow = handler(entry)
    assert flow.config_entry is entry
