"""Tests for deploy_diff.config."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from deploy_diff.config import Config, ConfigError, load_config


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_config(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "deploy_diff.json"
    p.write_text(json.dumps(data))
    return p


# ---------------------------------------------------------------------------
# defaults
# ---------------------------------------------------------------------------

def test_load_returns_config_instance(tmp_path):
    cfg = load_config(tmp_path / "missing.json")
    assert isinstance(cfg, Config)


def test_default_output_format_is_plain(tmp_path):
    cfg = load_config(tmp_path / "missing.json")
    assert cfg.default_output_format == "plain"


def test_default_retry_attempts(tmp_path):
    cfg = load_config(tmp_path / "missing.json")
    assert cfg.max_retry_attempts == 3


# ---------------------------------------------------------------------------
# file loading
# ---------------------------------------------------------------------------

def test_reads_cache_dir_from_file(tmp_path):
    p = _write_config(tmp_path, {"cache_dir": "/tmp/my_cache"})
    cfg = load_config(p)
    assert cfg.cache_dir == Path("/tmp/my_cache")


def test_reads_log_level_from_file(tmp_path):
    p = _write_config(tmp_path, {"log_level": "DEBUG"})
    cfg = load_config(p)
    assert cfg.log_level == "DEBUG"


def test_extra_keys_stored(tmp_path):
    p = _write_config(tmp_path, {"my_custom_key": 42})
    cfg = load_config(p)
    assert cfg.extra["my_custom_key"] == 42


def test_invalid_json_raises_config_error(tmp_path):
    bad = tmp_path / "deploy_diff.json"
    bad.write_text("not json{{{")
    with pytest.raises(ConfigError, match="Cannot parse"):
        load_config(bad)


def test_invalid_type_raises_config_error(tmp_path):
    p = _write_config(tmp_path, {"max_retry_attempts": "not-an-int"})
    with pytest.raises(ConfigError):
        load_config(p)


# ---------------------------------------------------------------------------
# env var
# ---------------------------------------------------------------------------

def test_env_var_overrides_default_path(tmp_path, monkeypatch):
    p = _write_config(tmp_path, {"log_level": "INFO"})
    monkeypatch.setenv("DEPLOY_DIFF_CONFIG", str(p))
    cfg = load_config()  # no explicit path
    assert cfg.log_level == "INFO"


def test_explicit_path_takes_priority_over_env(tmp_path, monkeypatch):
    env_cfg = _write_config(tmp_path, {"log_level": "ERROR"})
    explicit_cfg = tmp_path / "other.json"
    explicit_cfg.write_text(json.dumps({"log_level": "DEBUG"}))
    monkeypatch.setenv("DEPLOY_DIFF_CONFIG", str(env_cfg))
    cfg = load_config(explicit_cfg)
    assert cfg.log_level == "DEBUG"
