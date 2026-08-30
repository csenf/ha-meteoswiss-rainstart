"""MeteoSwiss website precipitation radar / INCA nowcast.

Samples the unofficial product JSON used by
https://www.meteoschweiz.admin.ch/service-und-publikationen/applikationen/niederschlag.html
(RZC measurements + INCA rate nowcast, ~1 km LV95 grid). Not a documented API.

Primary rain-start source for this integration: 5-minute frames at the home cell.
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

import httpx

from .api import DownloadError, ParseError, RainStartResult, lat_lon_to_lv95
from .const import (
    DATA_SOURCE_RADAR,
    MAX_RADAR_JSON_BYTES,
    PIPELINE_RADAR,
    RADAR_BASE_URL,
    RADAR_HOST,
    RADAR_PATH_PREFIX,
    TIMEZONE,
)

BASE = RADAR_BASE_URL
UA = {
    "User-Agent": "ha-meteoswiss-rainstart radar_nowcast (personal Home Assistant)"
}

# Legend lower bounds as painted by the website (mm/h)
LEGEND = [
    ("af00dd", 60.0, ">60"),
    ("ff1900", 40.0, "40-60"),
    ("ff7d01", 20.0, "20-40"),
    ("ffc703", 10.0, "10-20"),
    ("feff01", 6.0, "6-10"),
    ("05ff05", 4.0, "4-6"),
    ("058c2d", 2.0, "2-4"),
    ("0001fc", 1.0, "1-2"),
    ("9a7e95", 0.2, "0.2-1"),
    ("9e849a", 0.2, "0.2-1"),
]

_ZURICH = ZoneInfo(TIMEZONE)

DEFAULT_HOURS = 3.0


def lv95_to_grid_km(easting: float, northing: float) -> tuple[float, float]:
    """LV95 metres → CH km used in RZC/INCA JSON coords (6-digit km)."""
    e = easting / 1000.0
    n = northing / 1000.0
    if e >= 2000:
        e -= 2000.0
    if n >= 1000:
        n -= 1000.0
    return e, n


def color_to_rate(color: str) -> tuple[float, str]:
    c = color.lower().lstrip("#")
    if len(c) != 6:
        return 0.2, f"unknown:{c}"
    cr, cg, cb = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    best: tuple[float, str] | None = None
    best_d = 1e9
    for hexcol, lo, label in LEGEND:
        hr, hg, hb = int(hexcol[0:2], 16), int(hexcol[2:4], 16), int(hexcol[4:6], 16)
        d = abs(cr - hr) + abs(cg - hg) + abs(cb - hb)
        if d < best_d:
            best_d = d
            best = (lo, label)
    if best is None or best_d > 48:
        return 0.2, f"unknown:{c}"
    return best


def decode_ring(shape: dict, coords: dict) -> list[tuple[float, float]]:
    """Website chain-code → vertices in CH km (same space as coords)."""
    o = int(shape["i"])
    n = int(shape["j"])
    offs = shape.get("o") or ""
    d = shape.get("d") or ""
    x_min, x_max, x_count = coords["x_min"], coords["x_max"], coords["x_count"]
    y_min, y_max, y_count = coords["y_min"], coords["y_max"], coords["y_count"]
    ring: list[tuple[float, float]] = []
    s = 0
    while s < len(offs):
        frac = int(offs[s]) / 10.0 + 0.05
        if o % 2 == 0:
            a = x_min + (x_max - x_min) * (o / 2) / x_count
            i = y_min + (y_max - y_min) * ((n - 1) / 2 + frac) / y_count
        else:
            a = x_min + (x_max - x_min) * ((o - 1) / 2 + frac) / x_count
            i = y_min + (y_max - y_min) * (n / 2) / y_count
        ring.append((a, i))
        if 2 * s < len(d):
            o += ord(d[2 * s]) - 77
            n += ord(d[2 * s + 1]) - 77
        s += 1
    return ring


def point_in_ring(x: float, y: float, ring: list[tuple[float, float]]) -> bool:
    inside = False
    count = len(ring)
    if count < 3:
        return False
    j = count - 1
    for i in range(count):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > y) != (yj > y):
            denom = (yj - yi) if (yj - yi) != 0 else 1e-18
            if x < (xj - xi) * (y - yi) / denom + xi:
                inside = not inside
        j = i
    return inside


def sample_frame(frame: dict, x: float, y: float) -> dict:
    coords = frame["coords"]
    hits: list[dict] = []
    nearest = None
    nearest_d = 1e9
    for area in frame.get("areas") or []:
        color = area.get("color") or ""
        rate, label = color_to_rate(color)
        for poly in area.get("shapes") or []:
            for shp in poly:
                ring = decode_ring(shp, coords)
                if len(ring) < 3:
                    continue
                if point_in_ring(x, y, ring):
                    hits.append({"rate_lo": rate, "label": label, "color": color})
                cx = sum(p[0] for p in ring) / len(ring)
                cy = sum(p[1] for p in ring) / len(ring)
                dist = math.hypot(cx - x, cy - y)
                if dist < nearest_d:
                    nearest_d = dist
                    nearest = {
                        "km": dist,
                        "rate_lo": rate,
                        "label": label,
                        "color": color,
                    }
    if hits:
        hits.sort(key=lambda h: h["rate_lo"], reverse=True)
        top = hits[0]
        return {
            "wet": True,
            "rate_lo": top["rate_lo"],
            "label": top["label"],
            "color": top["color"],
            "nearest_km": 0.0,
        }
    if nearest:
        return {
            "wet": False,
            "rate_lo": 0.0,
            "label": "dry",
            "color": None,
            "nearest_km": nearest["km"],
            "nearest_label": nearest["label"],
        }
    return {
        "wet": False,
        "rate_lo": 0.0,
        "label": "empty",
        "color": None,
        "nearest_km": None,
    }


def select_pictures(pictures: list[dict], hours: float) -> list[dict]:
    meas = [p for p in pictures if p.get("data_type") == "measurement"]
    fcst = [p for p in pictures if p.get("data_type") == "forecast"]
    if not fcst and not meas:
        return pictures
    t0 = fcst[0]["timestamp"] if fcst else meas[-1]["timestamp"]
    t1 = t0 + int(hours * 3600)
    window = [p for p in fcst if p["timestamp"] <= t1]
    tail = meas[-3:] if meas else []
    return tail + window


def assess_parse_health(report: dict[str, Any]) -> tuple[bool, str]:
    """Detect unofficial JSON schema drift after a fetch still returned frames."""
    samples = report.get("samples") or []
    if not samples:
        return False, "no_frames"
    kinds = {sample.get("kind") for sample in samples}
    if not (kinds & {"measurement", "forecast"}):
        return False, "missing_frame_kinds"
    labels = [str(sample.get("label") or "empty") for sample in samples]
    if labels and all(label == "empty" for label in labels):
        return False, "all_frames_empty"
    if labels and all(label.startswith("unknown:") for label in labels):
        return False, "legend_mismatch"
    latest = report.get("now") or {}
    if latest.get("timestamp") is None:
        return False, "missing_now_timestamp"
    return True, "ok"


def _is_wet(sample: dict, threshold: float) -> bool:
    return bool(sample.get("wet")) and float(sample.get("rate_lo") or 0) >= threshold


def first_wet(samples: list[dict], threshold: float) -> dict | None:
    for sample in samples:
        if _is_wet(sample, threshold):
            return sample
    return None


def rain_end_from_samples(
    samples: list[dict],
    *,
    threshold: float,
    now: datetime,
) -> tuple[int | None, datetime | None]:
    """Minutes and clock until the current or next wet stretch goes dry."""
    ordered = sorted(
        (s for s in samples if s.get("timestamp") is not None),
        key=lambda s: int(s["timestamp"]),
    )
    if not ordered:
        return None, None

    start: int | None = None
    latest_meas_idx = next(
        (i for i in range(len(ordered) - 1, -1, -1) if ordered[i].get("kind") == "measurement"),
        None,
    )
    if latest_meas_idx is not None and _is_wet(ordered[latest_meas_idx], threshold):
        start = latest_meas_idx
    else:
        search_from = 0 if latest_meas_idx is None else latest_meas_idx + 1
        for index in range(search_from, len(ordered)):
            if _is_wet(ordered[index], threshold):
                start = index
                break

    if start is None:
        return None, None

    for sample in ordered[start + 1 :]:
        if not _is_wet(sample, threshold):
            rain_end = _to_zurich(int(sample["timestamp"]))
            minutes = max(0, int(round((rain_end - now).total_seconds() / 60)))
            return minutes, rain_end
    return None, None


def intensity_series_from_samples(samples: list[dict]) -> tuple[dict[str, Any], ...]:
    """Compact per-frame rates for the graph and sensor attribute."""
    series: list[dict[str, Any]] = []
    for sample in samples:
        if sample.get("timestamp") is None:
            continue
        ts = int(sample["timestamp"])
        series.append(
            {
                "timestamp": _to_zurich(ts).isoformat(),
                "rate_lo": float(sample.get("rate_lo") or 0),
                "wet": bool(sample.get("wet")),
                "kind": sample.get("kind") or "forecast",
                "label": sample.get("label") or ("dry" if not sample.get("wet") else ""),
            }
        )
    series.sort(key=lambda item: item["timestamp"])
    return tuple(series)


def _to_zurich(unix_s: int) -> datetime:
    return datetime.fromtimestamp(unix_s, tz=_ZURICH)


def _horizon_minutes(samples: list[dict]) -> int:
    ts = [int(s["timestamp"]) for s in samples if s.get("timestamp") is not None]
    if len(ts) < 2:
        return 0
    return max(1, int(round((max(ts) - min(ts)) / 60)))


def _step_minutes(samples: list[dict]) -> int:
    ts = sorted(
        int(s["timestamp"]) for s in samples if s.get("timestamp") is not None
    )
    if len(ts) < 2:
        return 5
    deltas = [b - a for a, b in zip(ts, ts[1:]) if b > a]
    if not deltas:
        return 5
    return max(1, int(round(min(deltas) / 60)))


def rain_start_from_report(
    report: dict[str, Any],
    *,
    threshold: float,
    now: datetime | None = None,
) -> RainStartResult:
    """Map a ping-style sample report to the coordinator payload."""
    ref = now or datetime.now(tz=_ZURICH)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=_ZURICH)
    else:
        ref = ref.astimezone(_ZURICH)

    latest = report.get("now") or {}
    first = report.get("first_wet")
    samples = report.get("samples") or []

    minutes: int | None = None
    rain_start: datetime | None = None
    intensity: float | None = None

    if _is_wet(latest, threshold):
        minutes = 0
        rain_start = _to_zurich(int(latest["timestamp"]))
        intensity = float(latest["rate_lo"])
    elif first is not None and _is_wet(first, threshold):
        rain_start = _to_zurich(int(first["timestamp"]))
        delta = (rain_start - ref).total_seconds() / 60
        minutes = max(0, int(round(delta)))
        intensity = float(first["rate_lo"])

    source_updated = ref
    if latest.get("timestamp") is not None:
        source_updated = _to_zurich(int(latest["timestamp"]))

    window_start = ""
    window_end = ""
    if samples:
        stamps = [int(s["timestamp"]) for s in samples if s.get("timestamp") is not None]
        if stamps:
            window_start = _to_zurich(min(stamps)).isoformat()
            window_end = _to_zurich(max(stamps)).isoformat()

    context: dict[str, str | int | float | None] = {
        "pipeline": str(PIPELINE_RADAR["pipeline"]),
        "collection": str(PIPELINE_RADAR["collection"]),
        "parameter": str(PIPELINE_RADAR["parameter"]),
        "step_minutes": _step_minutes(samples),
        "window_start": window_start,
        "window_end": window_end,
        "intensity_unit": "mm/h",
        "animation_version": report.get("animation_version") or "",
        "radar_time": source_updated.strftime("%H:%M"),
        "now_wet": bool(latest.get("wet")),
        "now_label": latest.get("label") or "dry",
    }
    raining = _is_wet(latest, threshold)
    precipitation = float(latest.get("rate_lo") or 0)
    nearest = latest.get("nearest_km")
    nearest_km = float(nearest) if nearest is not None else (0.0 if raining else None)
    if nearest is not None:
        context["nearest_km"] = float(nearest)

    minutes_until_dry, rain_end = rain_end_from_samples(
        samples, threshold=threshold, now=ref
    )
    series = intensity_series_from_samples(samples)

    return RainStartResult(
        minutes_until_rain=minutes,
        rain_start=rain_start,
        intensity=intensity,
        source_updated=source_updated,
        forecast_horizon_minutes=_horizon_minutes(samples),
        data_source=DATA_SOURCE_RADAR,
        forecast_context=context,
        raining=raining,
        precipitation=precipitation,
        nearest_km=nearest_km,
        minutes_until_dry=minutes_until_dry,
        rain_end=rain_end,
        intensity_series=series,
    )


def resolve_radar_url(path: str) -> str:
    """Resolve a relative or absolute product URL and reject anything off-host."""
    if path.startswith("https://") or path.startswith("http://"):
        url = path
    elif path.startswith("/"):
        url = BASE + path
    else:
        url = f"{BASE}/{path}"
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != RADAR_HOST:
        raise DownloadError(f"Blocked radar URL host: {parsed.hostname}")
    if not parsed.path.startswith(RADAR_PATH_PREFIX):
        raise DownloadError(f"Blocked radar URL path: {parsed.path}")
    return url


def _read_limited(response: httpx.Response, limit: int = MAX_RADAR_JSON_BYTES) -> bytes:
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_bytes():
        total += len(chunk)
        if total > limit:
            raise DownloadError("Radar nowcast response too large")
        chunks.append(chunk)
    return b"".join(chunks)


def _fetch_json(client: httpx.Client, path: str) -> Any:
    url = resolve_radar_url(path)
    try:
        with client.stream(
            "GET", url, headers=UA, timeout=30.0, follow_redirects=False
        ) as response:
            if response.status_code != 200:
                raise DownloadError(
                    f"Radar nowcast HTTP {response.status_code}: {url}"
                )
            length = response.headers.get("Content-Length")
            if length is not None and int(length) > MAX_RADAR_JSON_BYTES:
                raise DownloadError(f"Radar nowcast response too large: {url}")
            raw = _read_limited(response)
        return json.loads(raw)
    except DownloadError:
        raise
    except httpx.HTTPError as exc:
        raise DownloadError(f"Radar nowcast fetch failed: {url}") from exc
    except ValueError as exc:
        raise ParseError(f"Radar nowcast JSON invalid: {url}") from exc


def run_ping(
    easting: float,
    northing: float,
    *,
    hours: float,
    threshold: float,
    client: httpx.Client,
) -> dict[str, Any]:
    """Sample measurement + forecast frames at an LV95 pin."""
    x, y = lv95_to_grid_km(easting, northing)
    versions = _fetch_json(client, "/product/output/versions.json")
    try:
        anim_v = versions["precipitation/animation"]
    except (KeyError, TypeError) as exc:
        raise ParseError("versions.json missing precipitation/animation") from exc
    anim = _fetch_json(
        client,
        f"/product/output/precipitation/animation/version__{anim_v}/de/animation.json",
    )
    try:
        pictures = anim["map_images"][0]["pictures"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ParseError("animation.json missing map_images pictures") from exc

    selected = select_pictures(pictures, hours)
    samples: list[dict] = []
    for pic in selected:
        radar_url = pic.get("radar_url")
        if not radar_url:
            continue
        frame = _fetch_json(client, radar_url)
        try:
            hit = sample_frame(frame, x, y)
            ts = int(pic["timestamp"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ParseError(f"Radar nowcast frame invalid: {radar_url}") from exc
        hit.update(
            {
                "timestamp": ts,
                "time": _to_zurich(ts).strftime("%H:%M"),
                "kind": pic.get("data_type"),
                "day": pic.get("day"),
            }
        )
        samples.append(hit)

    if not samples:
        raise ParseError("Radar nowcast returned no frames")

    latest_meas = next(
        (s for s in reversed(samples) if s["kind"] == "measurement"), None
    )
    if latest_meas is None:
        latest_meas = samples[0]

    if _is_wet(latest_meas, threshold):
        wet = latest_meas
    else:
        wet = first_wet(
            [s for s in samples if s.get("kind") == "forecast"], threshold
        )

    return {
        "home": {"easting": easting, "northing": northing, "grid_km": [x, y]},
        "animation_version": anim_v,
        "inca_version": versions.get("inca/precipitation/rate"),
        "now": latest_meas,
        "first_wet": wet,
        "samples": samples,
        "threshold": threshold,
    }


def fetch_rain_start_radar(
    lat: float,
    lon: float,
    threshold: float,
    *,
    hours: float = DEFAULT_HOURS,
    http_client: httpx.Client | None = None,
) -> RainStartResult:
    """Fetch rain-start from website RZC/INCA JSON at lat/lon."""
    easting, northing = lat_lon_to_lv95(lat, lon)

    owned = http_client is None
    client = http_client or httpx.Client(timeout=60.0, follow_redirects=False)
    try:
        report = run_ping(
            easting,
            northing,
            hours=hours,
            threshold=threshold,
            client=client,
        )
        healthy, reason = assess_parse_health(report)
        if not healthy:
            raise ParseError(f"Radar nowcast sanity failed: {reason}")
        return rain_start_from_report(report, threshold=threshold)
    finally:
        if owned:
            client.close()
