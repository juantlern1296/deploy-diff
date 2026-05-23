"""Simple retry logic for transient failures (e.g. docker inspect, HTTP hooks)."""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Callable, Tuple, Type, TypeVar

log = logging.getLogger(__name__)

T = TypeVar("T")


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, attempts: int, last: Exception) -> None:
        super().__init__(f"Failed after {attempts} attempt(s): {last}")
        self.attempts = attempts
        self.last = last


@dataclass
class RetryPolicy:
    """Describes how retries should be performed."""

    max_attempts: int = 3
    delay: float = 1.0
    backoff: float = 2.0
    exceptions: Tuple[Type[Exception], ...] = field(default_factory=lambda: (Exception,))

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.delay < 0:
            raise ValueError("delay must be >= 0")
        if self.backoff < 1:
            raise ValueError("backoff must be >= 1")


def with_retry(fn: Callable[[], T], policy: RetryPolicy | None = None) -> T:
    """Call *fn* retrying on transient errors according to *policy*.

    Returns the return value of *fn* on success, or raises :class:`RetryError`
    once all attempts are exhausted.
    """
    if policy is None:
        policy = RetryPolicy()

    delay = policy.delay
    last_exc: Exception = RuntimeError("unreachable")

    for attempt in range(1, policy.max_attempts + 1):
        try:
            return fn()
        except policy.exceptions as exc:  # type: ignore[misc]
            last_exc = exc
            if attempt < policy.max_attempts:
                log.debug(
                    "Attempt %d/%d failed (%s); retrying in %.1fs",
                    attempt,
                    policy.max_attempts,
                    exc,
                    delay,
                )
                time.sleep(delay)
                delay *= policy.backoff
            else:
                log.debug(
                    "Attempt %d/%d failed (%s); giving up",
                    attempt,
                    policy.max_attempts,
                    exc,
                )

    raise RetryError(policy.max_attempts, last_exc)
