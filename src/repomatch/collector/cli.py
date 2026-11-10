"""Run discovery, enrichment, and export as one resumable collection."""

import argparse
import json
import logging
from pathlib import Path
import re
import sqlite3

from .config import load_config
from .discover import discover
from .enrich import enrich
from .environment import get_github_token
from .export import export_snapshot
from .github import GitHubClient, GitHubError
from .storage import Store

LOG = logging.getLogger(__name__)


def collect(root, name, limit=None):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", name):
        raise ValueError("Use 1–64 letters, digits, hyphens, or underscores for the snapshot name.")

    snapshot = root / "data/snapshots" / name
    if snapshot.exists():
        raise ValueError(f"Snapshot already exists: {snapshot}. Choose a new name.")

    config = load_config(root / "configs/collection.toml")
    if limit is not None and not 1 <= limit <= config.target_count:
        raise ValueError(f"--limit must be between 1 and {config.target_count}")

    store = Store(root / "data/working/runs" / name / "collector.sqlite3")
    try:
        needs_discovery = not store.count()
        if needs_discovery or store.pending_count():
            token = get_github_token(root)
            if not token:
                raise ValueError("Set GITHUB_TOKEN in .env or in your shell.")
            client = GitHubClient(token, config)

            if needs_discovery:
                candidates = discover(client, config, limit or config.target_count)
                if not candidates:
                    raise ValueError("No repositories found")
                store.seed(candidates)

            enrich(client, store, config)

        return export_snapshot(store, config, snapshot)
    finally:
        store.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="repomatch")
    parser.add_argument("command", choices=("collect",))
    parser.add_argument("--snapshot", required=True, help="Name for the new snapshot")
    parser.add_argument("--limit", type=int, help="Maximum candidates for a new run")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    try:
        result = collect(Path.cwd(), args.snapshot, args.limit)
    except (ValueError, OSError, sqlite3.Error, GitHubError) as error:
        LOG.error("%s", error)
        return 1
    except KeyboardInterrupt:
        LOG.warning("Interrupted. Rerun the same command to resume saved work.")
        return 130

    LOG.info("Wrote data/snapshots/%s/repos.jsonl", args.snapshot)
    print(json.dumps(result["collection_status"], indent=2))
    return 0
