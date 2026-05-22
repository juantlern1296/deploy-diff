"""Human-readable formatting for layer diffs."""

from typing import List
from .diff_engine import ChangeKind, LayerChange


DADD = "\033[32m+\033[0m"
DREMOVE = "\033[31m-\033[0m"
DMODIFY = "\033[33m~\033[0m"
DUNCHANGED = " "

_SYMBOLS = {
    ChangeKind.ADDED: DADD,
    ChangeKind.REMOVED: DREMOVE,
    ChangeKind.MODIFIED: DMODIFY,
    ChangeKind.UNCHANGED: DUNCHAGED if False else DUNCHAGED if False else " ",
}

_PLAIN_SYMBOLS = {
    ChangeKind.ADDED: "+",
    ChangeKind.REMOVED: "-",
    ChangeKind.MODIFIED: "~",
    ChangeKind.UNCHANGED: " ",
}


def format_change(change: LayerChange, color: bool = True) -> str:
    """Format a single LayerChange as a one-line string."""
    symbols = _PLAIN_SYMBOLS if not color else {
        ChangeKind.ADDED: "\033[32m+\033[0m",
        ChangeKind.REMOVED: "\033[31m-\033[0m",
        ChangeKind.MODIFIED: "\033[33m~\033[0m",
        ChangeKind.UNCHANGED: " ",
    }
    sym = symbols.get(change.kind, "?")
    digest = change.digest or "(empty)"
    cmd_preview = (change.created_by or "")[:72]
    if len(change.created_by or "") > 72:
        cmd_preview += "…"
    return f"{sym} [{digest}] {cmd_preview}"


def format_changelog(
    changes: List[LayerChange],
    image_from: str = "base",
    image_to: str = "target",
    color: bool = True,
) -> str:
    """Render a full changelog between two images."""
    lines: List[str] = []
    lines.append(f"deploy-diff: {image_from} → {image_to}")
    lines.append("=" * 60)

    if not changes:
        lines.append("  (no layers to compare)")
        return "\n".join(lines)

    counts = {k: 0 for k in ChangeKind}
    for change in changes:
        counts[change.kind] += 1
        lines.append(format_change(change, color=color))

    lines.append("-" * 60)
    summary_parts = []
    if counts[ChangeKind.ADDED]:
        summary_parts.append(f"{counts[ChangeKind.ADDED]} added")
    if counts[ChangeKind.REMOVED]:
        summary_parts.append(f"{counts[ChangeKind.REMOVED]} removed")
    if counts[ChangeKind.MODIFIED]:
        summary_parts.append(f"{counts[ChangeKind.MODIFIED]} modified")
    if counts[ChangeKind.UNCHANGED]:
        summary_parts.append(f"{counts[ChangeKind.UNCHANGED]} unchanged")
    lines.append("Summary: " + ", ".join(summary_parts) if summary_parts else "Summary: no changes")
    return "\n".join(lines)
