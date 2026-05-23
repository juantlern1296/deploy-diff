"""Tests for entrypoint_tracker and entrypoint_cli."""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

import pytest

from deploy_diff.entrypoint_tracker import (
    EntrypointDelta,
    EntrypointReport,
    _parse_cmd,
    build_entrypoint_report,
)
from deploy_diff.entrypoint_cli import cmd_entrypoint_diff


# ---------------------------------------------------------------------------
# EntrypointDelta
# ---------------------------------------------------------------------------

def test_delta_str_added():
    d = EntrypointDelta(old=None, new=["/bin/sh"])
    assert str(d).startswith("+")


def test_delta_str_removed():
    d = EntrypointDelta(old=["/bin/sh"], new=None)
    assert str(d).startswith("-")


def test_delta_str_modified():
    d = EntrypointDelta(old=["/bin/sh"], new=["/bin/bash"])
    assert "->" in str(d)


def test_is_added_flag():
    assert EntrypointDelta(old=None, new=["/app"]).is_added()
    assert not EntrypointDelta(old=["/app"], new=None).is_added()


def test_is_removed_flag():
    assert EntrypointDelta(old=["/app"], new=None).is_removed()
    assert not EntrypointDelta(old=None, new=["/app"]).is_removed()


def test_is_modified_flag():
    assert EntrypointDelta(old=["/a"], new=["/b"]).is_modified()
    assert not EntrypointDelta(old=None, new=["/b"]).is_modified()


# ---------------------------------------------------------------------------
# _parse_cmd
# ---------------------------------------------------------------------------

def test_parse_cmd_none_returns_none():
    assert _parse_cmd(None) is None


def test_parse_cmd_empty_list_returns_none():
    assert _parse_cmd([]) is None


def test_parse_cmd_list():
    assert _parse_cmd(["/bin/sh", "-c"]) == ["/bin/sh", "-c"]


def test_parse_cmd_string():
    assert _parse_cmd("/bin/sh") == ["/bin/sh"]


# ---------------------------------------------------------------------------
# build_entrypoint_report
# ---------------------------------------------------------------------------

def test_no_changes_returns_empty_report():
    cfg = {"Entrypoint": ["/app"], "Cmd": ["serve"]}
    report = build_entrypoint_report(cfg, cfg)
    assert not report.has_changes
    assert report.entrypoint is None
    assert report.cmd is None


def test_detects_entrypoint_change():
    old = {"Entrypoint": ["/bin/sh"], "Cmd": None}
    new = {"Entrypoint": ["/bin/bash"], "Cmd": None}
    report = build_entrypoint_report(old, new)
    assert report.entrypoint is not None
    assert report.entrypoint.is_modified()


def test_detects_cmd_change():
    cfg = {"Entrypoint": None, "Cmd": ["start"]}
    new = {"Entrypoint": None, "Cmd": ["run"]}
    report = build_entrypoint_report(cfg, new)
    assert report.cmd is not None


def test_summary_no_changes():
    cfg = {"Entrypoint": None, "Cmd": None}
    report = build_entrypoint_report(cfg, cfg)
    assert "No" in report.summary()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _write_config(tmp_path: Path, name: str, data: dict) -> str:
    p = tmp_path / name
    p.write_text(json.dumps(data))
    return str(p)


def test_cli_plain_output(tmp_path, capsys):
    old = _write_config(tmp_path, "old.json", {"Entrypoint": ["/a"], "Cmd": None})
    new = _write_config(tmp_path, "new.json", {"Entrypoint": ["/b"], "Cmd": None})
    args = argparse.Namespace(old_config=old, new_config=new, fmt="plain")
    rc = cmd_entrypoint_diff(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "ENTRYPOINT" in out


def test_cli_json_output(tmp_path, capsys):
    old = _write_config(tmp_path, "old.json", {"Entrypoint": ["/a"], "Cmd": ["x"]})
    new = _write_config(tmp_path, "new.json", {"Entrypoint": ["/a"], "Cmd": ["y"]})
    args = argparse.Namespace(old_config=old, new_config=new, fmt="json")
    rc = cmd_entrypoint_diff(args)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["has_changes"] is True


def test_cli_missing_file_returns_error(tmp_path):
    args = argparse.Namespace(
        old_config="/nonexistent/old.json",
        new_config="/nonexistent/new.json",
        fmt="plain",
    )
    rc = cmd_entrypoint_diff(args)
    assert rc == 1
