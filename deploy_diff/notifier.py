"""Notification hooks for deploy-diff reports.

Allows callers to register callbacks that fire when a report
is generated, e.g. to post to Slack or write to a webhook.
"""

from __future__ import annotations

import logging
from typing import Callable, Dict, List

from deploy_diff.reporter import Report

log = logging.getLogger(__name__)

# Registry: name -> callable(report: Report) -> None
_hooks: Dict[str, Callable[[Report], None]] = {}


class NotifierError(Exception):
    """Raised when a notification hook fails."""


def register_hook(name: str, fn: Callable[[Report], None]) -> None:
    """Register a notification hook under *name*.

    Raises NotifierError if *name* is already taken or *fn* is not callable.
    """
    if not callable(fn):
        raise NotifierError(f"Hook '{name}' must be callable, got {type(fn).__name__}")
    if name in _hooks:
        raise NotifierError(f"Hook '{name}' is already registered")
    _hooks[name] = fn
    log.debug("Registered notification hook: %s", name)


def unregister_hook(name: str) -> None:
    """Remove a previously registered hook. Silent if not found."""
    _hooks.pop(name, None)


def list_hooks() -> List[str]:
    """Return the names of all registered hooks."""
    return list(_hooks.keys())


def notify_all(report: Report, *, raise_on_error: bool = False) -> Dict[str, Exception]:
    """Fire every registered hook with *report*.

    Returns a mapping of hook-name -> exception for any hooks that raised.
    If *raise_on_error* is True, re-raises the first exception encountered.
    """
    errors: Dict[str, Exception] = {}
    for name, fn in list(_hooks.items()):
        try:
            fn(report)
            log.debug("Hook '%s' completed successfully", name)
        except Exception as exc:  # noqa: BLE001
            log.warning("Hook '%s' raised: %s", name, exc)
            errors[name] = exc
            if raise_on_error:
                raise
    return errors
