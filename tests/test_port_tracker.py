"""Tests for port_tracker and port_cli."""

from __future__ import annotations

import json
import os
import pytest

from deploy_diff.port_tracker import PortDelta, PortReport, build_port_report


# ---------------------------------------------------------------------------
# PortDelta helpers
# ---------------------------------------------------------------------------

def test_delta_str_added():
    d = PortDelta(port="8080/tcp", old_value=None, new_value="8080/tcp")
    assert str(d) == "+ 8080/tcp"


def test_delta_str_removed():
    d = PortDelta(port="443/tcp", old_value="443/tcp", new_value=None)
    assert str(d) == "- 443/tcp"


def test_delta_str_modified():
    d = PortDelta(port="80/tcp", old_value="80/tcp", new_value="80/tcp")
    assert str(d) == "~ 80/tcp (80/tcp -> 80/tcp)"


def test_is_added_flag():
    d = PortDelta(port="8080/tcp", old_value=None, new_value="8080/tcp")
    assert d.is_added
    assert not d.is_removed
    assert not d.is_modified


def test_is_removed_flag():
    d = PortDelta(port="8080/tcp", old_value="8080/tcp", new_value=None)
    assert d.is_removed
    assert not d.is_added


def test_is_modified_flag():
    d = PortDelta(port="8080/tcp", old_value="8080/tcp", new_value="8080/tcp")
    assert d.is_modified


# ---------------------------------------------------------------------------
# build_port_report
# ---------------------------------------------------------------------------

def test_empty_configs_return_empty_report():
    report = build_port_report({}, {})
    assert report.total == 0
    assert not report.has_changes()


def test_added_port_detected():
    old = {}
    new = {"ExposedPorts": {"8080/tcp": {}}}
    report = build_port_report(old, new)
    assert report.total == 1
    assert report.added[0].port == "8080/tcp"


def test_removed_port_detected():
    old = {"ExposedPorts": {"8080/tcp": {}}}
    new = {}
    report = build_port_report(old, new)
    assert report.total == 1
    assert report.removed[0].port == "8080/tcp"


def test_unchanged_ports_not_in_report():
    cfg = {"ExposedPorts": {"80/tcp": {}}}
    report = build_port_report(cfg, cfg)
    assert report.total == 0


def test_multiple_changes_sorted():
    old = {"ExposedPorts": {"80/tcp": {}, "443/tcp": {}}}
    new = {"ExposedPorts": {"443/tcp": {}, "9000/tcp": {}}}
    report = build_port_report(old, new)
    ports = [d.port for d in report.deltas]
    assert ports == sorted(ports)
    assert len(report.added) == 1
    assert len(report.removed) == 1


def test_non_dict_exposed_ports_treated_as_empty():
    old = {"ExposedPorts": None}
    new = {"ExposedPorts": {"8080/tcp": {}}}
    report = build_port_report(old, new)
    assert report.total == 1


# ---------------------------------------------------------------------------
# PortReport convenience properties
# ---------------------------------------------------------------------------

def test_report_added_removed_modified_partitions():
    deltas = [
        PortDelta("80/tcp", None, "80/tcp"),
        PortDelta("443/tcp", "443/tcp", None),
    ]
    r = PortReport(deltas=deltas)
    assert len(r.added) == 1
    assert len(r.removed) == 1
    assert len(r.modified) == 0
