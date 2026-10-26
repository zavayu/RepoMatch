"""Translate CLI arguments into collector operations.

The CLI owns resource setup and cleanup. Collection modules do not need to know
about terminal arguments, project-root resolution, or environment variables.
"""

import argparse
import json
import logging
from pathlib import Path
import re
import sqlite3

from .analyze import analyze_snapshot
from .config import load_config
from .dataset import generate_readable_copy
from .discover import discover
from .enrich import enrich
from .environment import get_github_token
from .export import export_snapshot
from .github import GitHubClient, GitHubError
from .storage import Store


def positive(value: str) -> int:
    """Argparse validator for limits, which must be greater than zero."""
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("Must be positive")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="repomatch")
    commands = parser.add_subparsers(dest="group", required=True)
    collect = commands.add_parser("collect")
    actions = collect.add_subparsers(dest="action", required=True)

    for action in ("discover", "enrich", "export", "analyze", "readable", "status"):
        command = actions.add_parser(action)
        command.add_argument(
            "--root",
            type=Path,
            default=Path.cwd(),
            help="Project root for all relative paths",
        )
        command.add_argument(
            "--config",
            type=Path,
            default=Path("configs/collection.toml"),
        )
        if action in {"discover", "enrich"}:
            command.add_argument("--limit", type=positive)
        if action == "enrich":
            command.add_argument("--retry-failed", action="store_true")
            command.add_argument("--refresh", action="store_true")
        if action in {"export", "analyze", "readable"}:
            command.add_argument("--snapshot", required=True)

    return parser


def snapshot_directory(root: Path, name: str) -> Path:
    """Keep snapshot names inside the project's snapshot directory."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", name):
        raise ValueError(
            "Snapshot name must use letters, numbers, underscores, "
            "or hyphens (max 64)"
        )
    return root / "data/snapshots" / name


def create_client(config, root: Path) -> GitHubClient:
    token = get_github_token(root)
    if not token:
        raise ValueError("Set GITHUB_TOKEN in the project .env file or your shell before collection")
    return GitHubClient(token, config)


def run_command(args):
    """Run one operation; analysis and readable copies need no token or database."""
    root = args.root.resolve()
    snapshot = None
    if args.action in {"export", "analyze", "readable"}:
        snapshot = snapshot_directory(root, args.snapshot)

    if args.action == "readable":
        return generate_readable_copy(snapshot)

    if args.action == "analyze":
        return analyze_snapshot(snapshot, root / "reports" / args.snapshot)

    config = load_config(root / args.config)
    client = None
    if args.action in {"discover", "enrich"}:
        client = create_client(config, root)

    store = Store(root / config.database)
    try:
        if args.action == "discover":
            count = discover(client, store, config, args.limit)
            return {"repository_count": count}

        if args.action == "enrich":
            processed = enrich(
                client,
                store,
                config,
                limit=args.limit,
                retry_failed=args.retry_failed,
                refresh=args.refresh,
            )
            return {"processed": processed, "status": store.stats()}

        if args.action == "export":
            return export_snapshot(store, config, snapshot)

        return store.stats()
    finally:
        # Close the database even when collection fails or the user presses Ctrl+C.
        store.close()


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        result = run_command(args)
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, sqlite3.Error, GitHubError, KeyError, TypeError) as error:
        logging.error("%s", error)
        return 1
    except KeyboardInterrupt:
        logging.warning(
            "Interrupted. Completed repositories and discovery progress are saved."
        )
        return 130

