"""Simple synchronous event bus for internal deploy-diff events."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


class EventBusError(Exception):
    """Raised when event bus operations fail."""


@dataclass
class Event:
    """Represents a single published event."""

    name: str
    payload: Any = None
    source: str = ""

    def __str__(self) -> str:  # pragma: no cover
        return f"Event(name={self.name!r}, source={self.source!r})"


# Registry: event_name -> list of handlers
_handlers: Dict[str, List[Callable[[Event], None]]] = defaultdict(list)


def subscribe(event_name: str, handler: Callable[[Event], None]) -> None:
    """Register *handler* to be called whenever *event_name* is published."""
    if not callable(handler):
        raise EventBusError(f"Handler for {event_name!r} must be callable.")
    if handler in _handlers[event_name]:
        raise EventBusError(
            f"Handler {handler!r} is already subscribed to {event_name!r}."
        )
    _handlers[event_name].append(handler)


def unsubscribe(event_name: str, handler: Callable[[Event], None]) -> None:
    """Remove *handler* from *event_name*.  Silently ignores unknown handlers."""
    try:
        _handlers[event_name].remove(handler)
    except ValueError:
        pass


def publish(event_name: str, payload: Any = None, source: str = "") -> int:
    """Dispatch *event_name* to all subscribers.  Returns the number of handlers called."""
    event = Event(name=event_name, payload=payload, source=source)
    called = 0
    for handler in list(_handlers.get(event_name, [])):
        handler(event)
        called += 1
    return called


def list_subscriptions(event_name: str) -> List[Callable[[Event], None]]:
    """Return a copy of the handler list for *event_name*."""
    return list(_handlers.get(event_name, []))


def clear(event_name: str | None = None) -> None:
    """Clear handlers for *event_name*, or all handlers if None."""
    if event_name is None:
        _handlers.clear()
    else:
        _handlers.pop(event_name, None)
