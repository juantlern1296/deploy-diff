"""Tests for the plugin registry."""
import pytest

from deploy_diff.plugin import (
    PluginError,
    get_formatter,
    list_formatters,
    load_plugin,
    register_formatter,
    unregister_formatter,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    """Ensure test-registered formatters are removed after each test."""
    yield
    for name in ("dummy", "slack", "html"):
        unregister_formatter(name)


def _dummy_formatter(report):
    return "dummy"


# ---------------------------------------------------------------------------
# register_formatter
# ---------------------------------------------------------------------------

def test_register_stores_callable():
    register_formatter("dummy", _dummy_formatter)
    assert get_formatter("dummy") is _dummy_formatter


def test_register_duplicate_raises():
    register_formatter("dummy", _dummy_formatter)
    with pytest.raises(PluginError, match="already registered"):
        register_formatter("dummy", _dummy_formatter)


def test_register_non_callable_raises():
    with pytest.raises(PluginError, match="must be callable"):
        register_formatter("dummy", "not_a_function")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# get_formatter / list_formatters
# ---------------------------------------------------------------------------

def test_get_unknown_returns_none():
    assert get_formatter("nonexistent") is None


def test_list_formatters_sorted():
    register_formatter("slack", _dummy_formatter)
    register_formatter("html", _dummy_formatter)
    names = list_formatters()
    assert "html" in names
    assert "slack" in names
    assert names == sorted(names)


# ---------------------------------------------------------------------------
# load_plugin
# ---------------------------------------------------------------------------

def test_load_plugin_bad_module_raises():
    with pytest.raises(PluginError, match="Cannot import plugin"):
        load_plugin("totally.nonexistent.module.xyz")


def test_load_plugin_valid_stdlib_module_does_not_raise():
    # Loading a stdlib module should succeed without error
    load_plugin("json")


# ---------------------------------------------------------------------------
# unregister_formatter
# ---------------------------------------------------------------------------

def test_unregister_removes_formatter():
    register_formatter("dummy", _dummy_formatter)
    unregister_formatter("dummy")
    assert get_formatter("dummy") is None


def test_unregister_missing_is_silent():
    # Should not raise even if name was never registered
    unregister_formatter("ghost")
