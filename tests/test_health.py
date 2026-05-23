"""Tests for deploy_diff.health."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from deploy_diff.health import (
    HealthResult,
    HealthReport,
    _check_docker,
    _check_cache_dir,
    run_health_checks,
)


# ---------------------------------------------------------------------------
# HealthResult
# ---------------------------------------------------------------------------

def test_health_result_str_ok():
    r = HealthResult("docker-cli", True, "daemon reachable")
    assert str(r) == "[OK] docker-cli — daemon reachable"


def test_health_result_str_fail_no_detail():
    r = HealthResult("cache-dir", False)
    assert str(r) == "[FAIL] cache-dir"


# ---------------------------------------------------------------------------
# HealthReport
# ---------------------------------------------------------------------------

def test_report_healthy_when_all_ok():
    report = HealthReport(results=[
        HealthResult("a", True),
        HealthResult("b", True),
    ])
    assert report.healthy is True


def test_report_unhealthy_when_any_fail():
    report = HealthReport(results=[
        HealthResult("a", True),
        HealthResult("b", False),
    ])
    assert report.healthy is False


def test_report_str_contains_overall():
    report = HealthReport(results=[HealthResult("x", True)])
    assert "Overall: healthy" in str(report)


# ---------------------------------------------------------------------------
# _check_docker
# ---------------------------------------------------------------------------

def test_check_docker_missing_cli():
    with patch("deploy_diff.health.shutil.which", return_value=None):
        result = _check_docker()
    assert result.ok is False
    assert "not found" in result.detail


def test_check_docker_daemon_reachable():
    with patch("deploy_diff.health.shutil.which", return_value="/usr/bin/docker"):
        with patch("deploy_diff.health.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = _check_docker()
    assert result.ok is True


def test_check_docker_daemon_unreachable():
    with patch("deploy_diff.health.shutil.which", return_value="/usr/bin/docker"):
        with patch(
            "deploy_diff.health.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "docker info"),
        ):
            result = _check_docker()
    assert result.ok is False


# ---------------------------------------------------------------------------
# _check_cache_dir
# ---------------------------------------------------------------------------

def test_check_cache_dir_writable(tmp_path):
    result = _check_cache_dir(str(tmp_path))
    assert result.ok is True


def test_check_cache_dir_not_writable(tmp_path):
    import os
    cache = tmp_path / "cache"
    cache.mkdir()
    cache.chmod(0o444)
    result = _check_cache_dir(str(cache))
    assert result.ok is False
    cache.chmod(0o755)  # restore so tmp_path cleanup works


# ---------------------------------------------------------------------------
# run_health_checks integration
# ---------------------------------------------------------------------------

def test_run_health_checks_returns_report(tmp_path):
    with patch("deploy_diff.health.shutil.which", return_value="/usr/bin/docker"):
        with patch("deploy_diff.health.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            report = run_health_checks(cache_dir=str(tmp_path))
    assert isinstance(report, HealthReport)
    assert len(report.results) == 2
