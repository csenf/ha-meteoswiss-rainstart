"""Diagnostics redaction tests."""

from meteoswiss_rainstart.diagnostics import TO_REDACT, redact_sensitive


def test_redact_sensitive_hides_coordinates():
    payload = {
        "entry": {"data": {"latitude": 46.89, "longitude": 7.50, "location_name": "Belp"}},
        "configured_location": {"latitude": 46.89, "longitude": 7.50},
        "parse_ok": True,
    }
    redacted = redact_sensitive(payload)
    assert redacted["entry"]["data"]["latitude"] == "**REDACTED**"
    assert redacted["entry"]["data"]["longitude"] == "**REDACTED**"
    assert redacted["configured_location"]["latitude"] == "**REDACTED**"
    assert redacted["entry"]["data"]["location_name"] == "Belp"
    assert redacted["parse_ok"] is True
    assert "latitude" in TO_REDACT
