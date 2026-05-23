"""Health check utilities for deploy-diff.

Provides a lightweight way to verify that required external dependencies
(Docker daemon, writable cache directory, etc.) are available before
running a full diff or snapshot operation.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from typing import List


@dataclass
class HealthResult:
    name: str
    ok: bool
    detail: str = ""

    def __str__(self) -> str:
        status = "OK" if self.ok else "FAIL"
        suffix = f" — {self.detail}" if self.detail else ""
        return f"[{status}] {self.name}{suffix}"


@dataclass
class HealthReport:
    results: List[HealthResult] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return all(r.ok for r in self.results)

    def __str__(self) -> str:
        lines = [str(r) for r in self.results]
        overall = "healthy" if self.healthy else "unhealthy"
        lines.append(f"Overall: {overall}")
        return "\n".join(lines)


def _check_docker() -> HealthResult:
    """Verify the Docker CLI is present and the daemon is reachable."""
    if shutil.which("docker") is None:
        return HealthResult("docker-cli", False, "'docker' not found on PATH")
    try:
        subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=5,
        )
        return HealthResult("docker-cli", True, "daemon reachable")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return HealthResult("docker-cli", False, str(exc))


def _check_cache_dir(cache_dir: str) -> HealthResult:
    """Verify the cache directory exists and is writable."""
    import os

    if not os.path.isdir(cache_dir):
        try:
            os.makedirs(cache_dir, exist_ok=True)
        except OSError as exc:
            return HealthResult("cache-dir", False, str(exc))
    if os.access(cache_dir, os.W_OK):
        return HealthResult("cache-dir", True, cache_dir)
    return HealthResult("cache-dir", False, f"not writable: {cache_dir}")


def run_health_checks(cache_dir: str = "/tmp/deploy_diff_cache") -> HealthReport:
    """Run all built-in health checks and return a consolidated report."""
    report = HealthReport()
    report.results.append(_check_docker())
    report.results.append(_check_cache_dir(cache_dir))
    return report
