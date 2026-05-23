"""Global configuration loader for deploy-diff.

Reads settings from environment variables and optional config files,
providing a single Config dataclass consumed by other modules.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

_CONFIG_FILE_ENV = "DEPLOY_DIFF_CONFIG"
_DEFAULT_CONFIG_FILE = Path("deploy_diff.json")


class ConfigError(Exception):
    """Raised when configuration is invalid."""


@dataclass
class Config:
    cache_dir: Path = Path(".deploy_diff_cache")
    snapshot_dir: Path = Path(".deploy_diff_snapshots")
    audit_dir: Path = Path(".deploy_diff_audit")
    default_output_format: str = "plain"
    max_retry_attempts: int = 3
    retry_delay: float = 1.0
    log_level: str = "WARNING"
    extra: Dict[str, Any] = field(default_factory=dict)


def _from_dict(data: Dict[str, Any]) -> Config:
    known = {
        "cache_dir", "snapshot_dir", "audit_dir",
        "default_output_format", "max_retry_attempts",
        "retry_delay", "log_level",
    }
    extra = {k: v for k, v in data.items() if k not in known}
    try:
        return Config(
            cache_dir=Path(data.get("cache_dir", ".deploy_diff_cache")),
            snapshot_dir=Path(data.get("snapshot_dir", ".deploy_diff_snapshots")),
            audit_dir=Path(data.get("audit_dir", ".deploy_diff_audit")),
            default_output_format=str(data.get("default_output_format", "plain")),
            max_retry_attempts=int(data.get("max_retry_attempts", 3)),
            retry_delay=float(data.get("retry_delay", 1.0)),
            log_level=str(data.get("log_level", "WARNING")),
            extra=extra,
        )
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Invalid configuration value: {exc}") from exc


def load_config(path: Optional[Path] = None) -> Config:
    """Load config from *path*, env-var override, or defaults."""
    resolved = path
    if resolved is None:
        env_path = os.environ.get(_CONFIG_FILE_ENV)
        resolved = Path(env_path) if env_path else _DEFAULT_CONFIG_FILE

    if resolved.exists():
        try:
            data = json.loads(resolved.read_text())
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Cannot parse config file {resolved}: {exc}") from exc
        return _from_dict(data)

    return Config()
