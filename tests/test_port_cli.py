"""Tests for port_cli module."""

from __future__ import annotations

import json
import os
import sys
import pytest

from deploy_diff.port_cli import main


def _write_config(tmp_path, name: str, data: dict) -> str:
    p = tmp_path / name
    p.write_text(json.dumps(data))
    return str(p)


def test_no_changes_plain(tmp_path, capsys):
    cfg = {"ExposedPorts": {"80/tcp": {}}}
    old = _write_config(tmp_path, "old.json", cfg)
    new = _write_config(tmp_path, "new.json", cfg)
    rc = main(["port-diff", old, new])
    out = capsys.readouterr().out
    assert rc == 0
    assert "No port changes" in out


def test_added_port_plain(tmp_path, capsys):
    old = _write_config(tmp_path, "old.json", {})
    new = _write_config(tmp_path, "new.json", {"ExposedPorts": {"8080/tcp": {}}})
    rc = main(["port-diff", old, new])
    out = capsys.readouterr().out
    assert rc == 0
    assert "+ 8080/tcp" in out


def test_removed_port_plain(tmp_path, capsys):
    old = _write_config(tmp_path, "old.json", {"ExposedPorts": {"8080/tcp": {}}})
    new = _write_config(tmp_path, "new.json", {})
    rc = main(["port-diff", old, new])
    out = capsys.readouterr().out
    assert rc == 0
    assert "- 8080/tcp" in out


def test_json_output(tmp_path, capsys):
    old = _write_config(tmp_path, "old.json", {})
    new = _write_config(tmp_path, "new.json", {"ExposedPorts": {"9000/tcp": {}}})
    rc = main(["port-diff", old, new, "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["port"] == "9000/tcp"
    assert data[0]["old"] is None


def test_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        main(["port-diff", "/no/such/old.json", "/no/such/new.json"])
    assert exc_info.value.code == 1


def test_no_subcommand_returns_one():
    rc = main([])
    assert rc == 1
