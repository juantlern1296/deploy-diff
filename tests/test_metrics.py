"""Tests for deploy_diff.metrics."""
import time
import pytest

from deploy_diff.metrics import (
    MetricsError,
    Counter,
    Timer,
    get_counter,
    get_timer,
    snapshot,
    reset_all,
)


@pytest.fixture(autouse=True)
def clean():
    reset_all()
    yield
    reset_all()


# --- Counter ---

def test_counter_starts_at_zero():
    c = Counter(name="hits")
    assert c.value == 0


def test_counter_increment_default():
    c = Counter(name="hits")
    c.increment()
    assert c.value == 1


def test_counter_increment_by_amount():
    c = Counter(name="hits")
    c.increment(5)
    assert c.value == 5


def test_counter_increment_negative_raises():
    c = Counter(name="hits")
    with pytest.raises(MetricsError):
        c.increment(-1)


def test_counter_reset():
    c = Counter(name="hits")
    c.increment(10)
    c.reset()
    assert c.value == 0


# --- Timer ---

def test_timer_stop_without_start_raises():
    t = Timer(name="op")
    with pytest.raises(MetricsError):
        t.stop()


def test_timer_records_elapsed():
    t = Timer(name="op")
    t.start()
    time.sleep(0.01)
    elapsed = t.stop()
    assert elapsed >= 0.01
    assert t.count == 1


def test_timer_average_none_when_empty():
    t = Timer(name="op")
    assert t.average is None


def test_timer_multiple_samples():
    t = Timer(name="op")
    for _ in range(3):
        t.start()
        t.stop()
    assert t.count == 3
    assert t.total > 0
    assert t.average == pytest.approx(t.total / 3, rel=1e-6)


def test_timer_reset_clears_samples():
    t = Timer(name="op")
    t.start()
    t.stop()
    t.reset()
    assert t.count == 0
    assert t.average is None


# --- Registry helpers ---

def test_get_counter_returns_same_instance():
    a = get_counter("reqs")
    b = get_counter("reqs")
    assert a is b


def test_get_timer_returns_same_instance():
    a = get_timer("load")
    b = get_timer("load")
    assert a is b


# --- Snapshot ---

def test_snapshot_includes_counter():
    get_counter("x").increment(3)
    s = snapshot()
    assert s["counters"]["x"] == 3


def test_snapshot_includes_timer_stats():
    t = get_timer("y")
    t.start()
    t.stop()
    s = snapshot()
    assert s["timers"]["y"]["count"] == 1
    assert s["timers"]["y"]["avg_s"] is not None


def test_reset_all_clears_everything():
    get_counter("c").increment()
    get_timer("t").start()
    get_timer("t").stop()
    reset_all()
    assert snapshot() == {"counters": {}, "timers": {}}
