"""Lightweight in-process metrics collection for deploy-diff operations."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class MetricsError(Exception):
    """Raised when metrics operations fail."""


@dataclass
class Counter:
    name: str
    value: int = 0

    def increment(self, amount: int = 1) -> None:
        if amount < 0:
            raise MetricsError(f"Counter increment must be non-negative, got {amount}")
        self.value += amount

    def reset(self) -> None:
        self.value = 0


@dataclass
class Timer:
    name: str
    _samples: List[float] = field(default_factory=list)
    _start: Optional[float] = field(default=None, repr=False)

    def start(self) -> None:
        self._start = time.monotonic()

    def stop(self) -> float:
        if self._start is None:
            raise MetricsError(f"Timer '{self.name}' stopped before it was started")
        elapsed = time.monotonic() - self._start
        self._samples.append(elapsed)
        self._start = None
        return elapsed

    @property
    def count(self) -> int:
        return len(self._samples)

    @property
    def total(self) -> float:
        return sum(self._samples)

    @property
    def average(self) -> Optional[float]:
        return self.total / self.count if self._samples else None

    def reset(self) -> None:
        self._samples.clear()
        self._start = None


_counters: Dict[str, Counter] = {}
_timers: Dict[str, Timer] = {}


def get_counter(name: str) -> Counter:
    if name not in _counters:
        _counters[name] = Counter(name=name)
    return _counters[name]


def get_timer(name: str) -> Timer:
    if name not in _timers:
        _timers[name] = Timer(name=name)
    return _timers[name]


def snapshot() -> dict:
    """Return a plain-dict snapshot of all current metric values."""
    return {
        "counters": {n: c.value for n, c in _counters.items()},
        "timers": {
            n: {"count": t.count, "total_s": round(t.total, 6), "avg_s": round(t.average, 6) if t.average is not None else None}
            for n, t in _timers.items()
        },
    }


def reset_all() -> None:
    """Clear all recorded metric data (useful in tests)."""
    _counters.clear()
    _timers.clear()
