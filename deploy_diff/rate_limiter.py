"""Simple token-bucket rate limiter for outbound notifications and API calls."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict


class RateLimitError(Exception):
    """Raised when a call is rejected due to rate limiting."""


@dataclass
class _Bucket:
    capacity: int
    refill_rate: float  # tokens per second
    tokens: float = field(init=False)
    last_refill: float = field(init=False)

    def __post_init__(self) -> None:
        self.tokens = float(self.capacity)
        self.last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def consume(self, amount: int = 1) -> bool:
        """Try to consume *amount* tokens. Returns True on success."""
        self._refill()
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


_buckets: Dict[str, _Bucket] = {}


def configure(name: str, *, capacity: int, refill_rate: float) -> None:
    """Create or replace a named rate-limit bucket."""
    if capacity <= 0:
        raise ValueError("capacity must be > 0")
    if refill_rate <= 0:
        raise ValueError("refill_rate must be > 0")
    _buckets[name] = _Bucket(capacity=capacity, refill_rate=refill_rate)


def check(name: str, amount: int = 1) -> bool:
    """Return True if the call is allowed, False if rate-limited."""
    if name not in _buckets:
        return True  # no limit configured — always allow
    return _buckets[name].consume(amount)


def require(name: str, amount: int = 1) -> None:
    """Like *check* but raises RateLimitError when the limit is exceeded."""
    if not check(name, amount):
        raise RateLimitError(f"Rate limit exceeded for '{name}'")


def remove(name: str) -> None:
    """Remove a named bucket (no-op if it does not exist)."""
    _buckets.pop(name, None)


def list_limiters() -> list[str]:
    """Return the names of all configured buckets."""
    return list(_buckets.keys())
