"""Tests for deploy_diff.rate_limiter."""

import pytest

from deploy_diff import rate_limiter as rl


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _clean():
    """Remove all buckets between tests."""
    for name in rl.list_limiters():
        rl.remove(name)


@pytest.fixture(autouse=True)
def clean_registry():
    _clean()
    yield
    _clean()


# ---------------------------------------------------------------------------
# configure
# ---------------------------------------------------------------------------


def test_configure_creates_bucket():
    rl.configure("slack", capacity=5, refill_rate=1.0)
    assert "slack" in rl.list_limiters()


def test_configure_raises_on_bad_capacity():
    with pytest.raises(ValueError, match="capacity"):
        rl.configure("x", capacity=0, refill_rate=1.0)


def test_configure_raises_on_bad_rate():
    with pytest.raises(ValueError, match="refill_rate"):
        rl.configure("x", capacity=1, refill_rate=0.0)


def test_configure_replaces_existing_bucket():
    rl.configure("a", capacity=1, refill_rate=1.0)
    rl.configure("a", capacity=10, refill_rate=5.0)
    # new bucket has 10 tokens — should allow 10 consecutive calls
    for _ in range(10):
        assert rl.check("a") is True


# ---------------------------------------------------------------------------
# check / require
# ---------------------------------------------------------------------------


def test_check_unknown_name_returns_true():
    assert rl.check("nonexistent") is True


def test_check_allows_up_to_capacity():
    rl.configure("test", capacity=3, refill_rate=0.01)
    assert rl.check("test") is True
    assert rl.check("test") is True
    assert rl.check("test") is True
    assert rl.check("test") is False  # bucket empty


def test_require_raises_when_limit_exceeded():
    rl.configure("strict", capacity=1, refill_rate=0.001)
    rl.require("strict")  # first call — OK
    with pytest.raises(rl.RateLimitError, match="strict"):
        rl.require("strict")


def test_require_passes_for_unknown_name():
    rl.require("ghost")  # should not raise


# ---------------------------------------------------------------------------
# remove / list
# ---------------------------------------------------------------------------


def test_remove_deletes_bucket():
    rl.configure("tmp", capacity=5, refill_rate=1.0)
    rl.remove("tmp")
    assert "tmp" not in rl.list_limiters()


def test_remove_noop_for_missing():
    rl.remove("does_not_exist")  # must not raise


def test_list_limiters_returns_all_names():
    rl.configure("a", capacity=1, refill_rate=1.0)
    rl.configure("b", capacity=2, refill_rate=2.0)
    names = rl.list_limiters()
    assert "a" in names
    assert "b" in names
