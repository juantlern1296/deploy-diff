"""CLI helpers for snapshot sub-commands (snap, compare-snap)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from deploy_diff.image_loader import ImageLoadError, load_image
from deploy_diff.snapshot import SnapshotError, Snapshot, list_snapshots, load_snapshot, save_snapshot


def _build_snap_parser(sub) -> None:
    p = sub.add_parser("snap", help="Save a snapshot of an image's layers")
    p.add_argument("image", help="Image reference, e.g. myrepo/app:v2")
    p.add_argument(
        "--snapshot-dir",
        default=None,
        metavar="DIR",
        help="Directory to store snapshots (default: ~/.deploy_diff/snapshots)",
    )


def _build_compare_snap_parser(sub) -> None:
    p = sub.add_parser("compare-snap", help="Compare a live image against a saved snapshot")
    p.add_argument("image", help="Current image reference")
    p.add_argument("snapshot", help="Snapshot reference to compare against")
    p.add_argument("--snapshot-dir", default=None, metavar="DIR")


def _build_list_snaps_parser(sub) -> None:
    sub.add_parser("list-snaps", help="List all saved snapshots")


def build_snapshot_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="deploy-diff-snap",
        description="Snapshot sub-commands for deploy-diff",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    _build_snap_parser(sub)
    _build_compare_snap_parser(sub)
    _build_list_snaps_parser(sub)
    return parser


def cmd_snap(args) -> int:
    try:
        manifest = load_image(args.image)
    except ImageLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    snap = Snapshot.from_manifest(manifest)
    directory = Path(args.snapshot_dir) if args.snapshot_dir else None
    path = save_snapshot(snap, directory=directory)
    print(f"Snapshot saved: {path}")
    return 0


def cmd_compare_snap(args) -> int:
    directory = Path(args.snapshot_dir) if args.snapshot_dir else None
    try:
        old_snap = load_snapshot(args.snapshot, directory=directory)
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    try:
        manifest = load_image(args.image)
    except ImageLoadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    new_snap = Snapshot.from_manifest(manifest)
    print(f"Snapshot: {old_snap.image_id[:12]}  →  Live: {new_snap.image_id[:12]}")
    old_digests = {l["digest"] for l in old_snap.layers}
    new_digests = {l["digest"] for l in new_snap.layers}
    added = new_digests - old_digests
    removed = old_digests - new_digests
    print(f"  Layers added:   {len(added)}")
    print(f"  Layers removed: {len(removed)}")
    return 0


def cmd_list_snaps(args) -> int:
    refs = list_snapshots()
    if not refs:
        print("No snapshots saved.")
    else:
        for ref in refs:
            print(ref)
    return 0


def main(argv=None) -> None:
    parser = build_snapshot_parser()
    args = parser.parse_args(argv)
    handlers = {"snap": cmd_snap, "compare-snap": cmd_compare_snap, "list-snaps": cmd_list_snaps}
    sys.exit(handlers[args.command](args))
