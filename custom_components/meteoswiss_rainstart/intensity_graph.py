"""SVG nowcast intensity graph (measurement + forecast bars)."""

from __future__ import annotations

from typing import Any, Mapping, Sequence
from xml.sax.saxutils import escape

WIDTH = 640
HEIGHT = 220
PAD_L = 44
PAD_R = 16
PAD_T = 24
PAD_B = 36


def render_intensity_svg(series: Sequence[Mapping[str, Any]]) -> str:
    """Render a self-contained SVG of cell intensity over the nowcast window."""
    if not series:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
            f'width="{WIDTH}" height="{HEIGHT}">'
            f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#f4f6f8"/>'
            '<text x="320" y="110" text-anchor="middle" fill="#6b7280" '
            'font-family="sans-serif" font-size="16">No data</text>'
            "</svg>"
        )

    rates = [max(0.0, float(item.get("rate_lo") or 0)) for item in series]
    ymax = max(4.0, max(rates))
    plot_w = WIDTH - PAD_L - PAD_R
    plot_h = HEIGHT - PAD_T - PAD_B
    n = len(series)
    bar_w = plot_w / n
    gap = min(3.0, bar_w * 0.15)

    bars: list[str] = []
    labels: list[str] = []
    for index, (item, rate) in enumerate(zip(series, rates)):
        x = PAD_L + index * bar_w + gap / 2
        h = 0.0 if ymax <= 0 else (rate / ymax) * plot_h
        y = PAD_T + plot_h - h
        kind = str(item.get("kind") or "forecast")
        fill = "#2563eb" if kind == "measurement" else "#38bdf8"
        if rate <= 0:
            fill = "#e5e7eb"
        bars.append(
            f'<rect class="{escape(kind)}" x="{x:.2f}" y="{y:.2f}" '
            f'width="{max(1.0, bar_w - gap):.2f}" height="{max(h, 1.0):.2f}" '
            f'fill="{fill}" rx="1"/>'
        )
        if index == 0 or index == n - 1 or index == n // 2:
            clock = _clock_label(item.get("timestamp"))
            lx = PAD_L + index * bar_w + bar_w / 2
            labels.append(
                f'<text x="{lx:.2f}" y="{HEIGHT - 12}" text-anchor="middle" '
                f'fill="#4b5563" font-family="sans-serif" font-size="11">'
                f"{escape(clock)}</text>"
            )

    ticks = []
    for value in (0.0, ymax / 2, ymax):
        ty = PAD_T + plot_h - (value / ymax) * plot_h
        ticks.append(
            f'<line x1="{PAD_L}" y1="{ty:.2f}" x2="{WIDTH - PAD_R}" y2="{ty:.2f}" '
            f'stroke="#e5e7eb" stroke-width="1"/>'
            f'<text x="{PAD_L - 6}" y="{ty + 4:.2f}" text-anchor="end" '
            f'fill="#6b7280" font-family="sans-serif" font-size="11">'
            f"{value:.0f}</text>"
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'width="{WIDTH}" height="{HEIGHT}">'
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#f4f6f8"/>'
        f'<text x="{PAD_L}" y="16" fill="#111827" font-family="sans-serif" '
        f'font-size="13">Intensity (mm/h)</text>'
        f"{''.join(ticks)}"
        f"{''.join(bars)}"
        f"{''.join(labels)}"
        '<text x="560" y="16" text-anchor="end" fill="#2563eb" '
        'font-family="sans-serif" font-size="11">measured</text>'
        '<text x="624" y="16" text-anchor="end" fill="#38bdf8" '
        'font-family="sans-serif" font-size="11">forecast</text>'
        "</svg>"
    )


def _clock_label(value: Any) -> str:
    text = str(value or "")
    if "T" in text and len(text) >= 16:
        return text[11:16]
    return text[:5] if text else ""
