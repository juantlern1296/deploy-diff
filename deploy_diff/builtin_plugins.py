"""Built-in optional formatters registered via the plugin system."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING

from deploy_diff.plugin import register_formatter

if TYPE_CHECKING:
    from deploy_diff.reporter import Report


# ---------------------------------------------------------------------------
# Markdown formatter
# ---------------------------------------------------------------------------

def _markdown_formatter(report: "Report") -> str:
    """Render a Report as a Markdown document."""
    lines: list[str] = []
    meta = report.meta
    lines.append(f"# Changelog: `{meta.from_ref}` → `{meta.to_ref}`")
    lines.append(f"_Generated: {meta.generated_at}_")
    lines.append("")

    s = report.summary
    lines.append(
        f"**Summary:** {s.total} change(s) — "
        f"+{s.added} added, -{s.removed} removed, ~{s.modified} modified"
    )
    lines.append("")

    if not report.changes:
        lines.append("_No layer changes detected._")
        return "\n".join(lines)

    lines.append("## Changes")
    lines.append("")
    symbol_map = {"added": "➕", "removed": "➖", "modified": "✏️"}
    for change in report.changes:
        symbol = symbol_map.get(change["kind"], "?")
        digest = change.get("digest", "")
        cmd = change.get("command", "")
        lines.append(f"- {symbol} `{digest}` — {cmd}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# JSON-lines formatter
# ---------------------------------------------------------------------------

def _jsonlines_formatter(report: "Report") -> str:
    """Render each change as a JSON object on its own line (NDJSON)."""
    out: list[str] = []
    for change in report.changes:
        out.append(json.dumps(change))
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Auto-register on import
# ---------------------------------------------------------------------------

def register_all() -> None:
    """Register all built-in formatters. Safe to call multiple times."""
    from deploy_diff.plugin import get_formatter

    if get_formatter("markdown") is None:
        register_formatter("markdown", _markdown_formatter)
    if get_formatter("jsonlines") is None:
        register_formatter("jsonlines", _jsonlines_formatter)
