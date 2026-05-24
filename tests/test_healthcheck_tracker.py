"""Tests for deploy_diff.healthcheck_tracker."""

import pytest

from deploy_diff.healthcheck_tracker import (
    HealthcheckDelta,
    HealthcheckReport,
    diff_healthcheck,
    _fmt,
)


def _layer(hc):
    return {"config": {"Healthcheck": hc}}


_HC_A = {"Test": ["CMD", "/bin/check"], "Interval": 30000000000, "Retries": 3}
_HC_B = {"Test": ["CMD", "/bin/probe"], "Interval": 60000000000, "Retries": 5}


def test_delta_str_added():
    d = HealthcheckDelta(old=None, new=_HC_A)
    assert "added" in str(d)


def test_delta_str_removed():
    d = HealthcheckDelta(old=_HC_A, new=None)
    assert "removed" in str(d)


def test_delta_str_modified():
    d = HealthcheckDelta(old=_HC_A, new=_HC_B)
    assert "->" in str(d)
    assert "changed" in str(d)


def test_is_added_flag():
    d = HealthcheckDelta(old=None, new=_HC_A)
    assert d.is_added
    assert not d.is_removed
    assert not d.is_modified


def test_is_removed_flag():
    d = HealthcheckDelta(old=_HC_A, new=None)
    assert d.is_removed
    assert not d.is_added
    assert not d.is_modified


def test_is_modified_flag():
    d = HealthcheckDelta(old=_HC_A, new=_HC_B)
    assert d.is_modified
    assert not d.is_added
    assert not d.is_removed


def test_no_changes_returns_empty_report():
    report = diff_healthcheck(_layer(_HC_A), _layer(_HC_A))
    assert not report.has_changes
    assert report.delta is None


def test_added_healthcheck_detected():
    report = diff_healthcheck(_layer(None), _layer(_HC_A))
    assert report.has_changes
    assert report.delta.is_added


def test_removed_healthcheck_detected():
    report = diff_healthcheck(_layer(_HC_A), _layer(None))
    assert report.has_changes
    assert report.delta.is_removed


def test_modified_healthcheck_detected():
    report = diff_healthcheck(_layer(_HC_A), _layer(_HC_B))
    assert report.has_changes
    assert report.delta.is_modified


def test_summary_no_changes():
    report = HealthcheckReport(delta=None)
    assert "No healthcheck" in report.summary()


def test_summary_with_change():
    delta = HealthcheckDelta(old=_HC_A, new=_HC_B)
    report = HealthcheckReport(delta=delta)
    assert "changed" in report.summary()


def test_fmt_none():
    assert _fmt(None) == "(none)"


def test_fmt_with_test_key():
    result = _fmt({"Test": ["CMD", "/healthz"], "Interval": 10, "Retries": 2})
    assert "/healthz" in result
    assert "interval=10" in result


def test_layer_with_uppercase_config_key():
    old = {"Config": {"Healthcheck": _HC_A}}
    new = {"Config": {"Healthcheck": _HC_B}}
    report = diff_healthcheck(old, new)
    assert report.has_changes
