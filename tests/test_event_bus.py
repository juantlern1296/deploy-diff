"""Tests for deploy_diff.event_bus and deploy_diff.event_bus_cli."""

from __future__ import annotations

import pytest

from deploy_diff import event_bus
from deploy_diff.event_bus import Event, EventBusError
from deploy_diff.event_bus_cli import build_event_parser, _cmd_list, _cmd_publish


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean():
    """Ensure a clean bus state for every test."""
    event_bus.clear()
    yield
    event_bus.clear()


# ---------------------------------------------------------------------------
# event_bus core
# ---------------------------------------------------------------------------

def test_subscribe_and_publish_calls_handler():
    received = []
    event_bus.subscribe("deploy.done", lambda e: received.append(e))
    event_bus.publish("deploy.done", payload={"tag": "v1"}, source="test")
    assert len(received) == 1
    assert received[0].name == "deploy.done"
    assert received[0].payload == {"tag": "v1"}


def test_publish_returns_handler_count():
    event_bus.subscribe("x", lambda e: None)
    event_bus.subscribe("x", lambda e: None)
    assert event_bus.publish("x") == 2


def test_publish_unknown_event_returns_zero():
    assert event_bus.publish("no.such.event") == 0


def test_subscribe_non_callable_raises():
    with pytest.raises(EventBusError, match="callable"):
        event_bus.subscribe("ev", "not_a_function")  # type: ignore[arg-type]


def test_subscribe_duplicate_raises():
    handler = lambda e: None  # noqa: E731
    event_bus.subscribe("ev", handler)
    with pytest.raises(EventBusError, match="already subscribed"):
        event_bus.subscribe("ev", handler)


def test_unsubscribe_removes_handler():
    calls = []
    handler = lambda e: calls.append(1)  # noqa: E731
    event_bus.subscribe("ev", handler)
    event_bus.unsubscribe("ev", handler)
    event_bus.publish("ev")
    assert calls == []


def test_unsubscribe_unknown_handler_is_silent():
    event_bus.unsubscribe("ev", lambda e: None)  # should not raise


def test_list_subscriptions_returns_copy():
    handler = lambda e: None  # noqa: E731
    event_bus.subscribe("ev", handler)
    subs = event_bus.list_subscriptions("ev")
    assert handler in subs
    subs.clear()  # mutating copy should not affect bus
    assert handler in event_bus.list_subscriptions("ev")


def test_clear_specific_event():
    event_bus.subscribe("a", lambda e: None)
    event_bus.subscribe("b", lambda e: None)
    event_bus.clear("a")
    assert event_bus.list_subscriptions("a") == []
    assert len(event_bus.list_subscriptions("b")) == 1


def test_clear_all():
    event_bus.subscribe("a", lambda e: None)
    event_bus.subscribe("b", lambda e: None)
    event_bus.clear()
    assert event_bus.list_subscriptions("a") == []
    assert event_bus.list_subscriptions("b") == []


def test_event_str():
    e = Event(name="foo", source="bar")
    assert "foo" in str(e)


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

class _FakeArgs:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


def test_cmd_list_no_handlers(capsys):
    args = _FakeArgs(event_name="ghost.event")
    rc = _cmd_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No handlers" in out


def test_cmd_list_with_handlers(capsys):
    def my_handler(e: Event) -> None:
        pass

    event_bus.subscribe("deploy.done", my_handler)
    args = _FakeArgs(event_name="deploy.done")
    rc = _cmd_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "my_handler" in out


def test_cmd_publish_returns_zero(capsys):
    args = _FakeArgs(event_name="deploy.done", source="test")
    rc = _cmd_publish(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "deploy.done" in out


def test_build_event_parser_has_subcommands():
    parser = build_event_parser()
    assert parser is not None
