"""Built-in notification hooks shipped with deploy-diff."""

from __future__ import annotations

import json
import logging
import urllib.request
from typing import Optional

from deploy_diff.reporter import Report
from deploy_diff.notifier import register_hook

log = logging.getLogger(__name__)


def _make_slack_hook(webhook_url: str):
    """Return a hook callable that POSTs a Slack message to *webhook_url*."""

    def _slack_hook(report: Report) -> None:
        summary = report.summary
        text = (
            f"*deploy-diff* report for `{report.meta.image_ref}`\n"
            f"Added: {summary.added}  Removed: {summary.removed}  "
            f"Modified: {summary.modified}  Unchanged: {summary.unchanged}"
        )
        payload = json.dumps({"text": text}).encode()
        req = urllib.request.Request(
            webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            log.debug("Slack webhook responded: %s", resp.status)

    return _slack_hook


def _make_log_hook(level: int = logging.INFO):
    """Return a hook callable that logs a one-line summary."""

    def _log_hook(report: Report) -> None:
        s = report.summary
        log.log(
            level,
            "deploy-diff [%s]: +%d -%d ~%d =%d",
            report.meta.image_ref,
            s.added,
            s.removed,
            s.modified,
            s.unchanged,
        )

    return _log_hook


def register_log_hook(name: str = "log", level: int = logging.INFO) -> None:
    """Register the built-in logging hook under *name*."""
    register_hook(name, _make_log_hook(level))


def register_slack_hook(webhook_url: str, name: str = "slack") -> None:
    """Register a Slack webhook hook under *name*."""
    if not webhook_url:
        raise ValueError("webhook_url must not be empty")
    register_hook(name, _make_slack_hook(webhook_url))
