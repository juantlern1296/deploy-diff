"""Plugin system for custom changelog formatters and reporters."""
from __future__ import annotations

import importlib
from typing import Callable, Dict, Optional

# Registry maps format name -> callable(report) -> str
_FORMAT_REGISTRY: Dict[str, Callable] = {}


class PluginError(Exception):
    """Raised when a plugin cannot be loaded or registered."""


def register_formatter(name: str, fn: Callable) -> None:
    """Register a named formatter callable.

    Args:
        name: Unique format identifier (e.g. 'slack', 'html').
        fn:   Callable that accepts a Report and returns a str.
    """
    if not callable(fn):
        raise PluginError(f"Formatter '{name}' must be callable, got {type(fn)}")
    if name in _FORMAT_REGISTRY:
        raise PluginError(f"Formatter '{name}' is already registered")
    _FORMAT_REGISTRY[name] = fn


def get_formatter(name: str) -> Optional[Callable]:
    """Return a registered formatter or None."""
    return _FORMAT_REGISTRY.get(name)


def list_formatters() -> list[str]:
    """Return sorted list of registered formatter names."""
    return sorted(_FORMAT_REGISTRY.keys())


def load_plugin(module_path: str) -> None:
    """Import a module by dotted path so its register calls execute.

    Args:
        module_path: e.g. 'my_package.deploy_diff_slack'
    """
    try:
        importlib.import_module(module_path)
    except ImportError as exc:
        raise PluginError(f"Cannot import plugin '{module_path}': {exc}") from exc


def unregister_formatter(name: str) -> None:
    """Remove a formatter from the registry (mainly for tests)."""
    _FORMAT_REGISTRY.pop(name, None)
