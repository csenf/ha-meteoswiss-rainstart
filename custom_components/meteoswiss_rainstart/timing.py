"""Poll and radar-age helpers (no Home Assistant imports)."""

from __future__ import annotations

from datetime import datetime, timedelta


def data_age_minutes(source_updated: datetime, now: datetime) -> int:
    """Minutes since the radar frame clock, never negative."""
    if source_updated.tzinfo is None:
        now = now.replace(tzinfo=None)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=source_updated.tzinfo)
    else:
        now = now.astimezone(source_updated.tzinfo)
    return max(0, int(round((now - source_updated).total_seconds() / 60)))


def next_fetch_at(last_fetch: datetime, interval_seconds: int) -> datetime:
    """Wall clock of the next coordinator poll."""
    return last_fetch + timedelta(seconds=interval_seconds)
