"""Collect a separate three-repository sample to check nested manifest coverage.

Run from the repository root: python scripts/check_nested_sample.py
Reads GITHUB_TOKEN from the shell or project .env; also supports public access.
The sample is deliberately selected for nested packages, .NET, and firmware.
"""

from dataclasses import replace
import json
import logging
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from repomatch.collector.analyze import analyze_snapshot
from repomatch.collector.config import Search, load_config
from repomatch.collector.dataset import generate_readable_copy, read_records
from repomatch.collector.enrich import enrich
from repomatch.collector.environment import get_github_token
from repomatch.collector.export import export_snapshot
from repomatch.collector.github import GitHubClient
from repomatch.collector.storage import Store

REPOSITORIES = (
    "prysmex/ember-eui",
    "arkane-systems/mousejiggler",
    "Stratolink-hq/Stratolink",
)


class SampleClient(GitHubClient):
    """Count logical API calls, including metadata used to seed the sample."""

    api_calls = 0

    def get(self, *args, **kwargs):
        self.api_calls += 1
        return super().get(*args, **kwargs)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    snapshot = ROOT / "data/snapshots/nested-sample"
    if snapshot.exists():
        raise ValueError("nested-sample already exists; inspect it before rerunning")

    searches = [
        Search(name=f"sample-{index}", query=f"repo:{name}", quota=1)
        for index, name in enumerate(REPOSITORIES)
    ]
    config = replace(
        load_config(ROOT / "configs/collection.toml"),
        database="data/working/nested-sample.sqlite3",
        target_count=len(REPOSITORIES),
        retries=0,
        searches=searches,
    )
    client = SampleClient(get_github_token(ROOT), config)
    store = Store(ROOT / config.database)
    started = time.monotonic()
    try:
        for name, search in zip(REPOSITORIES, searches):
            metadata = client.get("/repos/" + name)
            store.add(metadata, search)
        enrich(client, store, config)
        manifest = export_snapshot(store, config, snapshot)
    finally:
        store.close()

    analyze_snapshot(snapshot, ROOT / "reports/nested-sample")
    generate_readable_copy(snapshot)

    baseline_path = ROOT / "data/snapshots/pilot/repos.jsonl"
    baseline = {}
    if baseline_path.exists():
        baseline = {
            record["full_name"]: record for record in read_records(baseline_path)
        }

    comparisons = []
    for record in read_records(snapshot / "repos.jsonl"):
        collected = [
            item["path"] for item in record["manifests"].get("data", [])
            if item["status"] == "collected"
        ]
        previous = baseline.get(record["full_name"], {})
        previous_paths = [
            item["path"] for item in previous.get("manifests", {}).get("data", [])
            if item["status"] == "collected"
        ]
        comparisons.append({
            "repository": record["full_name"],
            "commit_sha": record["commit_sha"],
            "previous_pilot_paths": previous_paths,
            "collected_paths": collected,
            "nested_paths": [path for path in collected if "/" in path],
            "coverage": record["manifests"]["coverage"],
            "listing": record["listing"],
        })

    result = {
        "record_count": manifest["record_count"],
        "api_calls": client.api_calls,
        "elapsed_seconds": round(time.monotonic() - started, 2),
        "repositories": comparisons,
        "notes": [
            "Hand-selected functionality check, not a representative sample.",
            "Baseline pilot and current collection may use different commits.",
            "Logical API calls include candidate-seeding metadata requests.",
        ],
    }
    report = ROOT / "reports/nested-sample/sample-check.json"
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

