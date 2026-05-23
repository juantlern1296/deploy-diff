"""JSON schema definition and validator for deploy-diff config files.

Provides a lightweight schema dict and a validate_config helper that
returns a ValidationResult (compatible with schema_validator.py).
"""
from __future__ import annotations

from typing import Any, Dict

from deploy_diff.schema_validator import ValidationResult, validate

CONFIG_SCHEMA: Dict[str, Any] = {
    "required": [],
    "optional": [
        "cache_dir",
        "snapshot_dir",
        "audit_dir",
        "default_output_format",
        "max_retry_attempts",
        "retry_delay",
        "log_level",
    ],
    "types": {
        "cache_dir": str,
        "snapshot_dir": str,
        "audit_dir": str,
        "default_output_format": str,
        "max_retry_attempts": int,
        "retry_delay": (int, float),
        "log_level": str,
    },
    "allowed_values": {
        "default_output_format": ["plain", "json", "markdown", "jsonlines"],
        "log_level": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    },
}

_VALID_FORMATS = {"plain", "json", "markdown", "jsonlines"}
_VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def validate_config(doc: Dict[str, Any]) -> ValidationResult:
    """Return a ValidationResult for *doc* against the config schema."""
    errors: list[str] = []

    for key, expected in CONFIG_SCHEMA["types"].items():
        if key not in doc:
            continue
        if not isinstance(doc[key], expected):
            type_name = (
                " or ".join(t.__name__ for t in expected)
                if isinstance(expected, tuple)
                else expected.__name__
            )
            errors.append(
                f"'{key}' must be {type_name}, got {type(doc[key]).__name__}"
            )

    for key, allowed in CONFIG_SCHEMA["allowed_values"].items():
        if key in doc and doc[key] not in allowed:
            errors.append(
                f"'{key}' must be one of {allowed}, got {doc[key]!r}"
            )

    unknown = set(doc) - set(CONFIG_SCHEMA["optional"])
    # unknown keys are stored as 'extra' — not an error, just noted
    _ = unknown

    return ValidationResult(valid=len(errors) == 0, errors=errors)
