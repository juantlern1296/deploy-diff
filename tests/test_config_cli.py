"""Tests for deploy_diff.config_cli."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from deploy_diff.config_cli import _cmd_check, _cmd_show


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

class _Args:
    """Minimal namespace stand-in."""
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _write(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(data))
    return p


# ---------------------------------------------------------------------------
# cmd_show
# ---------------------------------------------------------------------------

def test_show_returns_zero_on_defaults(tmp_path, capsys):
    args = _Args(config=None)
    rc = _cmd_show(args)
    assert rc == 0


def test_show_prints_json(tmp_path, capsys):
    p = _write(tmp_path, {"log_level": "DEBUG"})
    args = _Args(config=str(p))
    _cmd_show(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["log_level"] == "DEBUG"


def test_show_returns_one_on_bad_file(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{{bad")
    args = _Args(config=str(bad))
    rc = _cmd_show(args)
    assert rc == 1


def test_show_includes_extra_keys(tmp_path, capsys):
    p = _write(tmp_path, {"my_flag": True})
    args = _Args(config=str(p))
    _cmd_show(args)
    out = json.loads(capsys.readouterr().out)
    assert out["extra"]["my_flag"] is True


# ---------------------------------------------------------------------------
# cmd_check
# ---------------------------------------------------------------------------

def test_check_returns_zero_for_valid(tmp_path, capsys):
    p = _write(tmp_path, {"log_level": "INFO"})
    args = _Args(file=str(p))
    rc = _cmd_check(args)
    assert rc == 0


def test_check_prints_ok(tmp_path, capsys):
    p = _write(tmp_path, {})
    args = _Args(file=str(p))
    _cmd_check(args)
    assert "OK" in capsys.readouterr().out


def test_check_returns_one_for_invalid(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("not json")
    args = _Args(file=str(bad))
    rc = _cmd_check(args)
    assert rc == 1


def test_check_prints_error_message(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text("{{")
    args = _Args(file=str(bad))
    _cmd_check(args)
    assert "error" in capsys.readouterr().err
