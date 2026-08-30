"""Tests for data-age and next-fetch helpers."""

from datetime import datetime, timedelta, timezone

from meteoswiss_rainstart.timing import data_age_minutes, next_fetch_at

ZURICH = timezone(timedelta(hours=2))


def test_data_age_rounds_to_minutes() -> None:
    source = datetime(2026, 8, 29, 21, 0, tzinfo=ZURICH)
    now = datetime(2026, 8, 29, 21, 8, tzinfo=ZURICH)
    assert data_age_minutes(source, now) == 8


def test_data_age_is_zero_when_source_is_in_the_future() -> None:
    source = datetime(2026, 8, 29, 21, 10, tzinfo=ZURICH)
    now = datetime(2026, 8, 29, 21, 8, tzinfo=ZURICH)
    assert data_age_minutes(source, now) == 0


def test_next_fetch_adds_poll_interval() -> None:
    last = datetime(2026, 8, 29, 21, 0, tzinfo=ZURICH)
    assert next_fetch_at(last, 300) == datetime(2026, 8, 29, 21, 5, tzinfo=ZURICH)
