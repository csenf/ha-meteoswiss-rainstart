"""Offline tests for the nowcast intensity SVG."""

from meteoswiss_rainstart.intensity_graph import render_intensity_svg


def test_empty_series_renders_svg() -> None:
    svg = render_intensity_svg([])
    assert svg.startswith("<svg")
    assert "no data" in svg.lower()


def test_bars_for_measurement_and_forecast() -> None:
    series = [
        {
            "timestamp": "2026-08-29T17:25:00+02:00",
            "rate_lo": 0.0,
            "kind": "measurement",
            "label": "dry",
        },
        {
            "timestamp": "2026-08-29T17:40:00+02:00",
            "rate_lo": 2.0,
            "kind": "forecast",
            "label": "2-4",
        },
    ]
    svg = render_intensity_svg(series)
    assert svg.startswith("<svg")
    assert "measurement" in svg
    assert "forecast" in svg
    assert svg.count("<rect") >= 2
