"""Handles writing Report output to files or stdout in various formats."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal, Optional, TextIO

from .reporter import Report

OutputFormat = Literal["text", "json"]


def write_report(
    report: Report,
    fmt: OutputFormat = "text",
    output_path: Optional[str] = None,
) -> None:
    """Write report to a file or stdout.

    Args:
        report: The Report to write.
        fmt: Output format, either 'text' or 'json'.
        output_path: File path to write to. If None, writes to stdout.
    """
    content = _render(report, fmt)
    if output_path is None:
        _write_to_stream(content, sys.stdout)
    else:
        _write_to_file(content, Path(output_path))


def _render(report: Report, fmt: OutputFormat) -> str:
    if fmt == "json":
        return report.to_json()
    return report.text


def _write_to_stream(content: str, stream: TextIO) -> None:
    stream.write(content)
    if not content.endswith("\n"):
        stream.write("\n")


def _write_to_file(content: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        fh.write(content)
        if not content.endswith("\n"):
            fh.write("\n")


def supported_formats() -> list[str]:
    """Return the list of supported output format identifiers."""
    return ["text", "json"]
