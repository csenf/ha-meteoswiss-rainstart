"""Offline tests for website radar nowcast (RZC + INCA JSON)."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from meteoswiss_rainstart.api import DownloadError, ParseError
from meteoswiss_rainstart.const import MAX_RADAR_JSON_BYTES
from meteoswiss_rainstart.radar_nowcast import (
    assess_parse_health,
    color_to_rate,
    decode_ring,
    first_wet,
    intensity_series_from_samples,
    lv95_to_grid_km,
    point_in_ring,
    rain_end_from_samples,
    rain_start_from_report,
    resolve_radar_url,
    sample_frame,
    select_pictures,
    _fetch_json,
)

BELP_EASTING = 2604360.5
BELP_NORTHING = 1194166.0

ZURICH = ZoneInfo("Europe/Zurich")


def test_lv95_belp() -> None:
    e, n = lv95_to_grid_km(BELP_EASTING, BELP_NORTHING)
    assert abs(e - 604.3605) < 1e-4
    assert abs(n - 194.166) < 1e-4


def test_legend_colors() -> None:
    assert color_to_rate("9a7e95")[0] == 0.2
    assert color_to_rate("#0001FC")[0] == 1.0
    assert color_to_rate("058c2d")[0] == 2.0
    assert color_to_rate("af00dd")[0] == 60.0
    assert color_to_rate("fff")[0] == 0.2
    assert color_to_rate("abcdef")[1].startswith("unknown:")


def test_point_in_ring() -> None:
    square = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]
    assert point_in_ring(1.0, 1.0, square)
    assert not point_in_ring(3.0, 1.0, square)


def test_first_wet_threshold() -> None:
    fake = [
        {"wet": False, "rate_lo": 0.0, "kind": "measurement", "time": "18:55"},
        {"wet": True, "rate_lo": 0.2, "kind": "forecast", "time": "19:25", "label": "0.2-1"},
        {"wet": True, "rate_lo": 1.0, "kind": "forecast", "time": "19:55", "label": "1-2"},
    ]
    assert first_wet(fake, 0.2)["time"] == "19:25"
    assert first_wet(fake, 1.0)["time"] == "19:55"
    assert first_wet(fake, 10.0) is None


def _synthetic_blob_frame(color: str = "0001fc") -> dict:
    coords = {
        "system": "LV95",
        "x_min": 0.0,
        "x_max": 10.0,
        "x_count": 10,
        "y_min": 0.0,
        "y_max": 10.0,
        "y_count": 10,
    }

    def ch(delta: int) -> str:
        return chr(77 + delta)

    offs = "0" * 16
    d = "".join(
        ch(v)
        for v in [
            2, 0, 2, 0, 2, 0, 2, 0,
            0, 2, 0, 2, 0, 2, 0, 2,
            -2, 0, -2, 0, -2, 0, -2, 0,
            0, -2, 0, -2, 0, -2, 0, -2,
        ]
    )
    shape = {"i": 4, "j": 5, "o": offs, "d": d, "l": 0}
    return {"coords": coords, "areas": [{"color": color, "shapes": [[shape]]}]}


def test_synthetic_blob_sample_inside_and_out() -> None:
    frame = _synthetic_blob_frame("0001fc")
    rings = []
    for area in frame["areas"]:
        for poly in area["shapes"]:
            for shp in poly:
                rings.append(decode_ring(shp, frame["coords"]))
    assert len(rings) == 1
    assert len(rings[0]) >= 8
    cx = sum(p[0] for p in rings[0]) / len(rings[0])
    cy = sum(p[1] for p in rings[0]) / len(rings[0])
    inside = sample_frame(frame, cx, cy)
    assert inside["wet"] is True
    assert inside["rate_lo"] == 1.0
    outside = sample_frame(frame, 0.3, 0.3)
    assert outside["wet"] is False


def test_select_pictures_window() -> None:
    pics = [
        {"data_type": "measurement", "timestamp": 1000},
        {"data_type": "measurement", "timestamp": 1300},
        {"data_type": "forecast", "timestamp": 1600},
        {"data_type": "forecast", "timestamp": 1600 + 2 * 3600},
        {"data_type": "forecast", "timestamp": 1600 + 4 * 3600},
    ]
    sel = select_pictures(pics, hours=3)
    assert all(
        p["timestamp"] <= 1600 + 3 * 3600 for p in sel if p["data_type"] == "forecast"
    )
    assert [p["data_type"] for p in sel].count("measurement") <= 3


def _ts(hour: int, minute: int) -> int:
    return int(datetime(2026, 8, 29, hour, minute, tzinfo=ZURICH).timestamp())


def test_rain_start_uses_forecast_when_measurement_dry() -> None:
    t_meas = _ts(17, 25)
    t_wet = _ts(17, 40)
    now = datetime(2026, 8, 29, 17, 35, tzinfo=ZURICH)
    report = {
        "now": {
            "wet": False,
            "rate_lo": 0.0,
            "label": "dry",
            "kind": "measurement",
            "timestamp": t_meas,
        },
        "first_wet": {
            "wet": True,
            "rate_lo": 1.0,
            "label": "1-2",
            "kind": "forecast",
            "timestamp": t_wet,
        },
        "samples": [
            {"timestamp": t_meas, "kind": "measurement"},
            {"timestamp": t_wet, "kind": "forecast"},
            {"timestamp": t_wet + 300, "kind": "forecast"},
        ],
        "animation_version": "20260829_1532",
        "threshold": 0.2,
    }
    result = rain_start_from_report(report, threshold=0.2, now=now)
    assert result.minutes_until_rain == 5
    assert result.intensity == 1.0
    assert result.data_source == "radar_nowcast"
    assert result.forecast_context["pipeline"] == "radar_nowcast"
    assert result.forecast_context["step_minutes"] == 5
    assert result.rain_start == datetime.fromtimestamp(t_wet, tz=ZURICH)


def test_rain_start_zero_when_already_raining() -> None:
    t_meas = _ts(17, 25)
    now = datetime(2026, 8, 29, 17, 35, tzinfo=ZURICH)
    report = {
        "now": {
            "wet": True,
            "rate_lo": 1.0,
            "label": "1-2",
            "kind": "measurement",
            "timestamp": t_meas,
        },
        "first_wet": {
            "wet": True,
            "rate_lo": 1.0,
            "label": "1-2",
            "kind": "measurement",
            "timestamp": t_meas,
        },
        "samples": [{"timestamp": t_meas, "kind": "measurement"}],
        "animation_version": "x",
        "threshold": 0.2,
    }
    result = rain_start_from_report(report, threshold=0.2, now=now)
    assert result.minutes_until_rain == 0
    assert result.intensity == 1.0
    assert result.source_updated == datetime.fromtimestamp(t_meas, tz=ZURICH)


def test_rain_start_unknown_when_horizon_dry() -> None:
    t_meas = _ts(17, 25)
    now = datetime(2026, 8, 29, 17, 35, tzinfo=ZURICH)
    report = {
        "now": {
            "wet": False,
            "rate_lo": 0.0,
            "label": "dry",
            "kind": "measurement",
            "timestamp": t_meas,
            "nearest_km": 12.0,
        },
        "first_wet": None,
        "samples": [
            {"timestamp": t_meas, "kind": "measurement"},
            {"timestamp": t_meas + 3600, "kind": "forecast"},
        ],
        "animation_version": "x",
        "threshold": 0.2,
    }
    result = rain_start_from_report(report, threshold=0.2, now=now)
    assert result.minutes_until_rain is None
    assert result.rain_start is None
    assert result.forecast_horizon_minutes == 60
    assert result.forecast_context["nearest_km"] == 12.0


def test_stale_wet_measurement_ignored_for_eta() -> None:
    """When latest measurement is dry, only walk forecast frames (same as ping)."""
    t_old_wet = _ts(16, 0)
    t_meas = _ts(17, 25)
    t_fcst = _ts(17, 50)
    now = datetime(2026, 8, 29, 17, 35, tzinfo=ZURICH)
    samples = [
        {
            "wet": True,
            "rate_lo": 2.0,
            "kind": "measurement",
            "timestamp": t_old_wet,
        },
        {
            "wet": False,
            "rate_lo": 0.0,
            "kind": "measurement",
            "timestamp": t_meas,
        },
        {
            "wet": True,
            "rate_lo": 0.2,
            "kind": "forecast",
            "timestamp": t_fcst,
        },
    ]
    latest_meas = samples[1]
    wet = first_wet([s for s in samples if s["kind"] == "forecast"], 0.2)
    report = {
        "now": latest_meas,
        "first_wet": wet,
        "samples": samples,
        "animation_version": "x",
        "threshold": 0.2,
    }
    result = rain_start_from_report(report, threshold=0.2, now=now)
    assert result.minutes_until_rain == 15
    assert result.intensity == 0.2
    assert result.raining is False
    assert result.precipitation == 0.0


def test_rain_end_after_current_wet_stretch() -> None:
    now = datetime(2026, 8, 29, 17, 35, tzinfo=ZURICH)
    t0 = _ts(17, 25)
    t_dry = _ts(17, 55)
    samples = [
        {"timestamp": t0, "wet": True, "rate_lo": 2.0, "kind": "measurement"},
        {"timestamp": t0 + 300, "wet": True, "rate_lo": 1.0, "kind": "forecast"},
        {"timestamp": t_dry, "wet": False, "rate_lo": 0.0, "kind": "forecast"},
    ]
    minutes, rain_end = rain_end_from_samples(samples, threshold=0.2, now=now)
    assert rain_end == datetime.fromtimestamp(t_dry, tz=ZURICH)
    assert minutes == 20


def test_rain_end_unknown_if_wet_through_horizon() -> None:
    now = datetime(2026, 8, 29, 17, 35, tzinfo=ZURICH)
    t0 = _ts(17, 25)
    samples = [
        {"timestamp": t0, "wet": True, "rate_lo": 2.0, "kind": "measurement"},
        {"timestamp": t0 + 600, "wet": True, "rate_lo": 1.0, "kind": "forecast"},
    ]
    minutes, rain_end = rain_end_from_samples(samples, threshold=0.2, now=now)
    assert minutes is None
    assert rain_end is None


def test_rain_end_after_future_event() -> None:
    now = datetime(2026, 8, 29, 17, 35, tzinfo=ZURICH)
    t_meas = _ts(17, 25)
    t_wet = _ts(17, 50)
    t_dry = _ts(18, 20)
    samples = [
        {"timestamp": t_meas, "wet": False, "rate_lo": 0.0, "kind": "measurement"},
        {"timestamp": t_wet, "wet": True, "rate_lo": 1.0, "kind": "forecast"},
        {"timestamp": t_dry, "wet": False, "rate_lo": 0.0, "kind": "forecast"},
    ]
    minutes, rain_end = rain_end_from_samples(samples, threshold=0.2, now=now)
    assert rain_end == datetime.fromtimestamp(t_dry, tz=ZURICH)
    assert minutes == 45


def test_report_maps_current_precip_and_series() -> None:
    t_meas = _ts(17, 25)
    t_wet = _ts(17, 40)
    now = datetime(2026, 8, 29, 17, 35, tzinfo=ZURICH)
    report = {
        "now": {
            "wet": False,
            "rate_lo": 0.0,
            "label": "dry",
            "kind": "measurement",
            "timestamp": t_meas,
            "nearest_km": 4.5,
        },
        "first_wet": {
            "wet": True,
            "rate_lo": 2.0,
            "label": "2-4",
            "kind": "forecast",
            "timestamp": t_wet,
        },
        "samples": [
            {
                "timestamp": t_meas,
                "wet": False,
                "rate_lo": 0.0,
                "kind": "measurement",
                "label": "dry",
            },
            {
                "timestamp": t_wet,
                "wet": True,
                "rate_lo": 2.0,
                "kind": "forecast",
                "label": "2-4",
            },
            {
                "timestamp": t_wet + 600,
                "wet": False,
                "rate_lo": 0.0,
                "kind": "forecast",
                "label": "dry",
            },
        ],
        "animation_version": "x",
        "threshold": 0.2,
    }
    result = rain_start_from_report(report, threshold=0.2, now=now)
    assert result.raining is False
    assert result.precipitation == 0.0
    assert result.nearest_km == 4.5
    assert result.minutes_until_dry == 15
    assert len(result.intensity_series) == 3
    assert result.intensity_series[1]["rate_lo"] == 2.0
    assert result.intensity_series[1]["kind"] == "forecast"


def test_parse_health_ok_for_normal_report() -> None:
    t_meas = _ts(17, 25)
    report = {
        "now": {"timestamp": t_meas, "wet": False, "label": "dry"},
        "samples": [
            {"timestamp": t_meas, "kind": "measurement", "label": "dry"},
            {"timestamp": t_meas + 300, "kind": "forecast", "label": "dry"},
        ],
        "animation_version": "20260829",
    }
    assert assess_parse_health(report) == (True, "ok")


def test_parse_health_fails_without_frames() -> None:
    assert assess_parse_health({"now": {}, "samples": []}) == (False, "no_frames")


def test_parse_health_fails_when_all_frames_empty() -> None:
    report = {
        "now": {"timestamp": 1, "label": "empty"},
        "samples": [
            {"timestamp": 1, "kind": "measurement", "label": "empty"},
            {"timestamp": 2, "kind": "forecast", "label": "empty"},
        ],
        "animation_version": "x",
    }
    assert assess_parse_health(report) == (False, "all_frames_empty")


def test_intensity_series_skips_missing_timestamps() -> None:
    t0 = _ts(17, 25)
    series = intensity_series_from_samples(
        [
            {"rate_lo": 0.0, "wet": False, "kind": "measurement"},
            {
                "timestamp": t0,
                "rate_lo": 1.0,
                "wet": True,
                "kind": "forecast",
                "label": "1-2",
            },
        ]
    )
    assert len(series) == 1
    assert series[0]["rate_lo"] == 1.0
    assert series[0]["kind"] == "forecast"


def test_resolve_radar_url_allows_relative_product_path() -> None:
    url = resolve_radar_url("/product/output/versions.json")
    assert url == "https://www.meteoschweiz.admin.ch/product/output/versions.json"


def test_resolve_radar_url_rejects_other_hosts() -> None:
    with pytest.raises(DownloadError, match="Blocked radar URL host"):
        resolve_radar_url("https://evil.example/product/output/x.json")


def test_resolve_radar_url_rejects_http_and_wrong_path() -> None:
    with pytest.raises(DownloadError, match="Blocked radar URL host"):
        resolve_radar_url("http://www.meteoschweiz.admin.ch/product/output/x.json")
    with pytest.raises(DownloadError, match="Blocked radar URL path"):
        resolve_radar_url("https://www.meteoschweiz.admin.ch/other/x.json")


def test_run_ping_raises_parse_when_versions_missing_animation() -> None:
    import httpx

    from meteoswiss_rainstart.radar_nowcast import run_ping

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"other": "x"})

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)
    with pytest.raises(ParseError, match="precipitation/animation"):
        run_ping(BELP_EASTING, BELP_NORTHING, hours=1, threshold=0.2, client=client)


def test_fetch_json_rejects_redirect_and_oversize() -> None:
    import httpx

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("redirect.json"):
            return httpx.Response(302, headers={"location": "https://evil.example/x"})
        if request.url.path.endswith("big.json"):
            return httpx.Response(
                200,
                headers={"Content-Length": str(MAX_RADAR_JSON_BYTES + 1)},
                content=b"{}",
            )
        if request.url.path.endswith("bad.json"):
            return httpx.Response(200, content=b"not-json")
        return httpx.Response(200, json={"ok": True})

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=False)
    assert _fetch_json(client, "/product/output/ok.json") == {"ok": True}
    with pytest.raises(DownloadError, match="HTTP 302"):
        _fetch_json(client, "/product/output/redirect.json")
    with pytest.raises(DownloadError, match="too large"):
        _fetch_json(client, "/product/output/big.json")
    with pytest.raises(ParseError, match="JSON invalid"):
        _fetch_json(client, "/product/output/bad.json")


def test_parse_health_fails_on_legend_mismatch() -> None:
    report = {
        "now": {"timestamp": 1, "label": "unknown:abcdef"},
        "samples": [
            {"timestamp": 1, "kind": "measurement", "label": "unknown:abcdef"},
            {"timestamp": 2, "kind": "forecast", "label": "unknown:123456"},
        ],
        "animation_version": "x",
    }
    assert assess_parse_health(report) == (False, "legend_mismatch")
