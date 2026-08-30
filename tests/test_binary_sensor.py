"""Regression tests for the parser_problem "what to do" translation lookup.

Home Assistant's real ``async_get_cached_translations(hass, language,
category, integration=None)`` builds its own ``{integration}`` set
internally, so ``integration`` must be a single domain string. Passing a
set (as the old code did) makes that become ``{{DOMAIN}}``, a set
containing a set, which raises ``TypeError: cannot use 'set' as a set
element (unhashable type)`` as soon as the cache is actually consulted -
something the default test stub (which has no
``async_get_cached_translations`` at all) never exercised.
"""

from __future__ import annotations

from meteoswiss_rainstart import binary_sensor
from meteoswiss_rainstart.binary_sensor import _WHAT_TO_DO_FALLBACK, _resolve_what_to_do
from meteoswiss_rainstart.const import DOMAIN


class _FakeConfig:
    def __init__(self, language: str) -> None:
        self.language = language


class _FakeHass:
    def __init__(self, language: str = "en") -> None:
        self.config = _FakeConfig(language)


def test_resolve_what_to_do_calls_cache_with_domain_string_not_a_set(monkeypatch) -> None:
    calls = []

    def fake_async_get_cached_translations(hass, language, category, integration=None):
        calls.append((hass, language, category, integration))
        return {}

    monkeypatch.setattr(
        binary_sensor.translation,
        "async_get_cached_translations",
        fake_async_get_cached_translations,
        raising=False,
    )

    hass = _FakeHass("de")
    _resolve_what_to_do(hass)

    assert len(calls) == 1
    _, language, category, integration = calls[0]
    assert language == "de"
    assert category == "common"
    assert integration == DOMAIN
    assert isinstance(integration, str)


def test_resolve_what_to_do_uses_translated_string_when_present(monkeypatch) -> None:
    key = f"component.{DOMAIN}.parser_problem.what_to_do"

    def fake_async_get_cached_translations(hass, language, category, integration=None):
        return {key: "Translated hint"}

    monkeypatch.setattr(
        binary_sensor.translation,
        "async_get_cached_translations",
        fake_async_get_cached_translations,
        raising=False,
    )

    assert _resolve_what_to_do(_FakeHass()) == "Translated hint"


def test_resolve_what_to_do_falls_back_when_key_missing(monkeypatch) -> None:
    def fake_async_get_cached_translations(hass, language, category, integration=None):
        return {}

    monkeypatch.setattr(
        binary_sensor.translation,
        "async_get_cached_translations",
        fake_async_get_cached_translations,
        raising=False,
    )

    assert _resolve_what_to_do(_FakeHass()) == _WHAT_TO_DO_FALLBACK


def test_resolve_what_to_do_falls_back_when_cache_helper_unavailable(monkeypatch) -> None:
    monkeypatch.delattr(binary_sensor.translation, "async_get_cached_translations", raising=False)

    assert _resolve_what_to_do(_FakeHass()) == _WHAT_TO_DO_FALLBACK
