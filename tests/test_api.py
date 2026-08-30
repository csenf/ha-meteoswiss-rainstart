"""Unit tests for meteoswiss_rainstart.api."""

from __future__ import annotations

import pytest

from meteoswiss_rainstart.api import (
    OutOfBoundsError,
    RainStartResult,
    fetch_rain_start,
    is_within_switzerland,
    lat_lon_to_lv95,
)


class TestSwitzerlandBounds:
    def test_belp_is_inside(self) -> None:
        assert is_within_switzerland(46.8986, 7.49578)

    def test_berlin_is_outside(self) -> None:
        assert not is_within_switzerland(52.52, 13.405)


class TestLatLonToLv95:
    def test_belp_coordinates(self) -> None:
        east, north = lat_lon_to_lv95(46.8986, 7.49578)
        assert 2_600_000 < east < 2_610_000
        assert 1_190_000 < north < 1_200_000


def test_fetch_rain_start_rejects_outside_switzerland() -> None:
    with pytest.raises(OutOfBoundsError):
        fetch_rain_start(52.52, 13.405, threshold=0.1)


def test_fetch_rain_start_passes_through_parse_error(monkeypatch) -> None:
    from meteoswiss_rainstart import api as api_mod
    from meteoswiss_rainstart.api import ParseError

    def _boom(*_args, **_kwargs):
        raise ParseError("sanity failed")

    monkeypatch.setattr(
        "meteoswiss_rainstart.radar_nowcast.fetch_rain_start_radar",
        _boom,
    )
    with pytest.raises(ParseError, match="sanity failed"):
        api_mod.fetch_rain_start(46.8986, 7.49578, threshold=0.1)


@pytest.mark.integration
def test_live_fetch_rain_start() -> None:
    result = fetch_rain_start(46.8986, 7.49578, threshold=0.1)
    assert isinstance(result, RainStartResult)
    assert result.data_source == "radar_nowcast"
    assert result.forecast_horizon_minutes > 0
