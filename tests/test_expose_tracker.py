"""Tests for expose_tracker and expose_cli."""
from __future__ import annotations

import json
import io
import types
from unittest.mock import patch

import pytest

from deploy_diff.expose_tracker import (
    ExposeDelta,
    ExposeReport,
    diff_exposed_ports,
)
from deploy_diff.expose_cli import cmd_expose_diff


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _layer(ports):
    """Create a minimal fake LayerInfo with exposed_ports."""
    obj = types.SimpleNamespace(exposed_ports=ports)
    return obj


# ---------------------------------------------------------------------------
# ExposeDelta
# ---------------------------------------------------------------------------

def test_delta_str_added():
    d = ExposeDelta(key="8080/tcp", old_value=None, new_value="")
    assert str(d) == "+ 8080/tcp"


def test_delta_str_removed():
    d = ExposeDelta(key="443/tcp", old_value="", new_value=None)
    assert str(d) == "- 443/tcp"


def test_delta_str_modified():
    d = ExposeDelta(key="80/tcp", old_value="old", new_value="new")
    assert "~" in str(d)
    assert "80/tcp" in str(d)


def test_is_added_flag():
    d = ExposeDelta(key="8080/tcp", old_value=None, new_value="")
    assert d.is_added()
    assert not d.is_removed()
    assert not d.is_modified()


def test_is_removed_flag():
    d = ExposeDelta(key="8080/tcp", old_value="", new_value=None)
    assert d.is_removed()
    assert not d.is_added()


# ---------------------------------------------------------------------------
# diff_exposed_ports
# ---------------------------------------------------------------------------

def test_no_changes_returns_empty_report():
    old = _layer({"80/tcp": {}, "443/tcp": {}})
    new = _layer({"80/tcp": {}, "443/tcp": {}})
    report = diff_exposed_ports(old, new)
    assert report.is_empty()
    assert report.total == 0


def test_added_port_detected():
    old = _layer({"80/tcp": {}})
    new = _layer({"80/tcp": {}, "8080/tcp": {}})
    report = diff_exposed_ports(old, new)
    assert len(report.added) == 1
    assert report.added[0].key == "8080/tcp"


def test_removed_port_detected():
    old = _layer({"80/tcp": {}, "9000/tcp": {}})
    new = _layer({"80/tcp": {}})
    report = diff_exposed_ports(old, new)
    assert len(report.removed) == 1
    assert report.removed[0].key == "9000/tcp"


def test_none_layers_treated_as_empty():
    report = diff_exposed_ports(None, None)
    assert report.is_empty()


def test_list_based_exposed_ports():
    old = _layer(["80/tcp"])
    new = _layer(["80/tcp", "443/tcp"])
    report = diff_exposed_ports(old, new)
    assert len(report.added) == 1


# ---------------------------------------------------------------------------
# cmd_expose_diff
# ---------------------------------------------------------------------------

def _args(old, new, fmt="plain"):
    return types.SimpleNamespace(old_config=old, new_config=new, output_format=fmt)


def test_cmd_no_changes_prints_message(tmp_path):
    cfg = json.dumps({"config": {"ExposedPorts": {"80/tcp": {}}}, "rootfs": {"diff_ids": ["sha256:abc"]}})
    old_f = tmp_path / "old.json"
    new_f = tmp_path / "new.json"
    old_f.write_text(cfg)
    new_f.write_text(cfg)
    out = io.StringIO()
    rc = cmd_expose_diff(_args(str(old_f), str(new_f)), out=out)
    assert rc == 0
    assert "No changes" in out.getvalue()


def test_cmd_json_output(tmp_path):
    old_cfg = json.dumps({"config": {"ExposedPorts": {"80/tcp": {}}}, "rootfs": {"diff_ids": ["sha256:aaa"]}})
    new_cfg = json.dumps({"config": {"ExposedPorts": {"80/tcp": {}, "8080/tcp": {}}}, "rootfs": {"diff_ids": ["sha256:bbb"]}})
    old_f = tmp_path / "old.json"
    new_f = tmp_path / "new.json"
    old_f.write_text(old_cfg)
    new_f.write_text(new_cfg)
    out = io.StringIO()
    rc = cmd_expose_diff(_args(str(old_f), str(new_f), fmt="json"), out=out)
    assert rc == 0
    data = json.loads(out.getvalue())
    assert isinstance(data, list)
    assert any(item["key"] == "8080/tcp" for item in data)
