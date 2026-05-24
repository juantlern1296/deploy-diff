"""Tracks changes to the USER instruction between two Docker image configs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from deploy_diff.diff_engine import LayerChange, ChangeKind


@dataclass
class UserDelta:
    old_user: Optional[str]
    new_user: Optional[str]

    def __str__(self) -> str:
        if self.is_added:
            return f"user added: {self.new_user}"
        if self.is_removed:
            return f"user removed: {self.old_user}"
        return f"user changed: {self.old_user!r} -> {self.new_user!r}"

    @property
    def is_added(self) -> bool:
        return self.old_user is None and self.new_user is not None

    @property
    def is_removed(self) -> bool:
        return self.old_user is not None and self.new_user is None

    @property
    def is_modified(self) -> bool:
        return (
            self.old_user is not None
            and self.new_user is not None
            and self.old_user != self.new_user
        )


@dataclass
class UserReport:
    delta: Optional[UserDelta]

    @property
    def has_changes(self) -> bool:
        return self.delta is not None

    def summary(self) -> str:
        if not self.has_changes:
            return "No USER changes."
        return str(self.delta)


def build_user_report(changes: List[LayerChange]) -> UserReport:
    """Extract USER-related changes from a list of LayerChange objects."""
    user_changes = [
        c for c in changes if c.label.lower().startswith("user")
    ]
    if not user_changes:
        return UserReport(delta=None)

    change = user_changes[-1]
    if change.kind == ChangeKind.ADDED:
        delta = UserDelta(old_user=None, new_user=change.new_value)
    elif change.kind == ChangeKind.REMOVED:
        delta = UserDelta(old_user=change.old_value, new_user=None)
    else:
        delta = UserDelta(old_user=change.old_value, new_user=change.new_value)

    return UserReport(delta=delta)


def diff_users(old_user: Optional[str], new_user: Optional[str]) -> UserReport:
    """Compare USER values directly and return a UserReport."""
    old = old_user or None
    new = new_user or None
    if old == new:
        return UserReport(delta=None)
    return UserReport(delta=UserDelta(old_user=old, new_user=new))
