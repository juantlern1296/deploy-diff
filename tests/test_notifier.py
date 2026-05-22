"""Tests for deploy_diff.notifier and deploy_diff.builtin_notifiers."""

from __future__ import annotations

import logging
import pytest

from deploy_diff.notifier import (
    NotifierError,
    list_hooks,
    notify_all,
    register_hook,
    unregister_hook,
)
from deploy_diff.reporter import Report, ReportMeta, ReportSummary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_report() -> Report:
    meta = ReportMeta(image_ref="nginx:latest", base_ref=None, generated_at="2024-01-01T00:00:00")
    summary = ReportSummary(added=1, removed=0, modified=2, unchanged=5)
    return Report(meta=meta, summary=summary, changes=[])


@pytest.fixture(autouse=True)
def _clean_hooks():
    """Isolate the hook registry between tests."""
    from deploy_diff import notifier
    original = dict(notifier._hooks)
    notifier._hooks.clear()
    yield
    notifier._hooks.clear()
    notifier._hooks.update(original)


# ---------------------------------------------------------------------------
# register_hook
# ---------------------------------------------------------------------------

def test_register_stores_callable():
    fn = lambda r: None  # noqa: E731
    register_hook("test", fn)
    assert "test" in list_hooks()


def test_register_duplicate_raises():
    register_hook("dup", lambda r: None)
    with pytest.raises(NotifierError, match="already registered"):
        register_hook("dup", lambda r: None)


def test_register_non_callable_raises():
    with pytest.raises(NotifierError, match="must be callable"):
        register_hook("bad", "not-a-function")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# unregister_hook / list_hooks
# ---------------------------------------------------------------------------

def test_unregister_removes_hook():
    register_hook("temp", lambda r: None)
    unregister_hook("temp")
    assert "temp" not in list_hooks()


def test_unregister_missing_is_silent():
    unregister_hook("ghost")  # should not raise


def test_list_hooks_empty_by_default():
    assert list_hooks() == []


# ---------------------------------------------------------------------------
# notify_all
# ---------------------------------------------------------------------------

def test_notify_all_calls_each_hook():
    called = []
    register_hook("h1", lambda r: called.append("h1"))
    register_hook("h2", lambda r: called.append("h2"))
    notify_all(_fake_report())
    assert sorted(called) == ["h1", "h2"]


def test_notify_all_returns_errors_dict():
    def _bad(r):
        raise RuntimeError("boom")

    register_hook("bad", _bad)
    errors = notify_all(_fake_report())
    assert "bad" in errors
    assert isinstance(errors["bad"], RuntimeError)


def test_notify_all_raise_on_error():
    register_hook("explode", lambda r: (_ for _ in ()).throw(ValueError("oops")))
    with pytest.raises(ValueError, match="oops"):
        notify_all(_fake_report(), raise_on_error=True)


# ---------------------------------------------------------------------------
# builtin_notifiers
# ---------------------------------------------------------------------------

def test_register_log_hook(caplog):
    from deploy_diff.builtin_notifiers import register_log_hook

    register_log_hook("mylog", level=logging.INFO)
    assert "mylog" in list_hooks()
    with caplog.at_level(logging.INFO):
        notify_all(_fake_report())
    assert "nginx:latest" in caplog.text


def test_register_slack_hook_empty_url_raises():
    from deploy_diff.builtin_notifiers import register_slack_hook

    with pytest.raises(ValueError, match="webhook_url"):
        register_slack_hook("")
