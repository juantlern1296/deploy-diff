"""Tests for deploy_diff.retry and deploy_diff.retry_cli."""

from __future__ import annotations

import argparse
import pytest

from deploy_diff.retry import RetryError, RetryPolicy, with_retry
from deploy_diff.retry_cli import add_retry_arguments, policy_from_args


# ---------------------------------------------------------------------------
# RetryPolicy validation
# ---------------------------------------------------------------------------

def test_policy_defaults():
    p = RetryPolicy()
    assert p.max_attempts == 3
    assert p.delay == 1.0
    assert p.backoff == 2.0


def test_policy_raises_on_zero_attempts():
    with pytest.raises(ValueError, match="max_attempts"):
        RetryPolicy(max_attempts=0)


def test_policy_raises_on_negative_delay():
    with pytest.raises(ValueError, match="delay"):
        RetryPolicy(delay=-0.1)


def test_policy_raises_on_backoff_below_one():
    with pytest.raises(ValueError, match="backoff"):
        RetryPolicy(backoff=0.5)


# ---------------------------------------------------------------------------
# with_retry success paths
# ---------------------------------------------------------------------------

def test_success_on_first_attempt():
    calls = []

    def fn():
        calls.append(1)
        return "ok"

    result = with_retry(fn, RetryPolicy(max_attempts=3, delay=0))
    assert result == "ok"
    assert len(calls) == 1


def test_success_after_transient_failure():
    attempts = []

    def fn():
        attempts.append(1)
        if len(attempts) < 3:
            raise OSError("transient")
        return "done"

    policy = RetryPolicy(max_attempts=5, delay=0, exceptions=(OSError,))
    result = with_retry(fn, policy)
    assert result == "done"
    assert len(attempts) == 3


# ---------------------------------------------------------------------------
# with_retry failure paths
# ---------------------------------------------------------------------------

def test_raises_retry_error_after_exhaustion():
    def fn():
        raise ValueError("boom")

    policy = RetryPolicy(max_attempts=3, delay=0)
    with pytest.raises(RetryError) as exc_info:
        with_retry(fn, policy)

    assert exc_info.value.attempts == 3
    assert isinstance(exc_info.value.last, ValueError)


def test_non_matching_exception_propagates_immediately():
    """Exceptions not in policy.exceptions should bubble up without retry."""
    calls = []

    def fn():
        calls.append(1)
        raise TypeError("unexpected")

    policy = RetryPolicy(max_attempts=5, delay=0, exceptions=(OSError,))
    with pytest.raises(TypeError):
        with_retry(fn, policy)

    assert len(calls) == 1


def test_default_policy_used_when_none():
    """Passing policy=None should fall back to default RetryPolicy."""
    calls = []

    def fn():
        calls.append(1)
        return 42

    assert with_retry(fn) == 42


# ---------------------------------------------------------------------------
# retry_cli helpers
# ---------------------------------------------------------------------------

def _parse(*argv: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    add_retry_arguments(parser)
    return parser.parse_args(list(argv))


def test_cli_defaults_produce_valid_policy():
    args = _parse()
    policy = policy_from_args(args)
    assert policy.max_attempts == 3
    assert policy.delay == 1.0
    assert policy.backoff == 2.0


def test_cli_custom_values_respected():
    args = _parse("--retry-attempts", "5", "--retry-delay", "0.5", "--retry-backoff", "1.5")
    policy = policy_from_args(args)
    assert policy.max_attempts == 5
    assert policy.delay == 0.5
    assert policy.backoff == 1.5
