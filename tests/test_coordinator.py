"""Coordinator helper tests (no live Home Assistant)."""

from datetime import datetime, timezone
from types import SimpleNamespace

from meteoswiss_rainstart.api import DownloadError, OutOfBoundsError, ParseError
from meteoswiss_rainstart.const import (
    FETCH_STATUS_DOWNLOAD_ERROR,
    FETCH_STATUS_ERROR,
    FETCH_STATUS_OUT_OF_BOUNDS,
    FETCH_STATUS_PARSE_ERROR,
)
from meteoswiss_rainstart.coordinator import (
    MeteoSwissRainStartCoordinator,
    classify_update_error,
)


def test_classify_update_error():
    assert classify_update_error(OutOfBoundsError("x")) == (
        FETCH_STATUS_OUT_OF_BOUNDS,
        False,
    )
    assert classify_update_error(DownloadError("x")) == (
        FETCH_STATUS_DOWNLOAD_ERROR,
        False,
    )
    assert classify_update_error(ParseError("x")) == (FETCH_STATUS_PARSE_ERROR, True)
    assert classify_update_error(RuntimeError("bug")) == (FETCH_STATUS_ERROR, False)


def test_diagnostics_snapshot_omits_forecast_point():
    entry = SimpleNamespace(
        data={
            "latitude": 46.8986,
            "longitude": 7.49578,
            "threshold_mm": 0.1,
            "poll_interval": 300,
            "location_name": "Belp",
        }
    )
    coordinator = MeteoSwissRainStartCoordinator(SimpleNamespace(), entry)
    coordinator.last_fetch_at = datetime(2026, 8, 29, 21, 0, tzinfo=timezone.utc)
    coordinator.data_source = "radar_nowcast"
    snapshot = coordinator.diagnostics_snapshot
    assert "forecast_point" not in snapshot
    assert snapshot["configured_location"]["latitude"] == 46.8986
    assert snapshot["location_name"] == "Belp"
