"""JSON schema validation for deploy-diff configuration and report structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ValidationError(Exception):
    """Raised when a document fails schema validation."""


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]

    def __bool__(self) -> bool:
        return self.valid

    def __str__(self) -> str:
        if self.valid:
            return "OK"
        return "Invalid: " + "; ".join(self.errors)


_REPORT_SCHEMA: dict[str, Any] = {
    "required": ["meta", "summary", "changes"],
    "meta": {
        "required": ["generated_at", "image_a", "image_b"],
        "types": {"generated_at": str, "image_a": str, "image_b": str},
    },
    "summary": {
        "required": ["added", "removed", "modified", "total"],
        "types": {"added": int, "removed": int, "modified": int, "total": int},
    },
    "changes": {"is_list": True},
}


def _check_keys(doc: dict[str, Any], required: list[str]) -> list[str]:
    return [f"missing key '{k}'" for k in required if k not in doc]


def _check_types(doc: dict[str, Any], types: dict[str, type]) -> list[str]:
    errors = []
    for key, expected in types.items():
        if key in doc and not isinstance(doc[key], expected):
            errors.append(
                f"'{key}' expected {expected.__name__}, got {type(doc[key]).__name__}"
            )
    return errors


def validate_report(doc: Any) -> ValidationResult:
    """Validate a report dict against the expected structure."""
    errors: list[str] = []

    if not isinstance(doc, dict):
        return ValidationResult(False, ["document must be a mapping"])

    errors += _check_keys(doc, _REPORT_SCHEMA["required"])
    if errors:
        return ValidationResult(False, errors)

    for section in ("meta", "summary"):
        spec = _REPORT_SCHEMA[section]
        sub = doc.get(section, {})
        if not isinstance(sub, dict):
            errors.append(f"'{section}' must be a mapping")
            continue
        errors += _check_keys(sub, spec["required"])
        errors += _check_types(sub, spec["types"])

    if not isinstance(doc.get("changes"), list):
        errors.append("'changes' must be a list")

    return ValidationResult(len(errors) == 0, errors)


def assert_valid_report(doc: Any) -> None:
    """Validate and raise ValidationError if invalid."""
    result = validate_report(doc)
    if not result:
        raise ValidationError(str(result))
