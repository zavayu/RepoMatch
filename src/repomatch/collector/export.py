"""Export immutable snapshots with canonical JSONL and a checksum."""

import json
import os
from pathlib import Path
import shutil
import tempfile

from .dataset import file_checksum, write_records
from .models import SCHEMA_VERSION, now


def export_snapshot(store, config, directory: Path):
    """Publish a snapshot only after every record and its manifest are written."""
    if directory.exists():
        raise ValueError(
            f"Snapshot already exists: {directory}. Choose a new name."
        )

    directory.parent.mkdir(parents=True, exist_ok=True)
    # Write beside the destination, then rename on the same filesystem. A failed
    # export must not leave a snapshot directory that looks complete.
    staging = Path(
        tempfile.mkdtemp(prefix=".snapshot-", dir=directory.parent)
    )
    try:
        dataset_path = staging / "repos.jsonl"
        count = write_records(store.records(), dataset_path)

        if count == 0:
            raise ValueError("No collected records to export")

        manifest = {
            "schema_version": SCHEMA_VERSION,
            "created_at": now(),
            "record_count": count,
            "dataset_file": dataset_path.name,
            "sha256": file_checksum(dataset_path),
            "dataset_bytes": dataset_path.stat().st_size,
            "config": config.to_dict(),
            "collection_status": store.stats(),
            "notes": [
                "Partial records retain explicit failure states.",
                "Source files are pinned per repository; "
                "language statistics are fetched live.",
                "Search ordering and GitHub content can change "
                "between collection runs.",
            ],
        }
        manifest_path = staging / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        os.rename(staging, directory)
        return manifest
    finally:
        # After a successful rename, staging no longer exists.
        if staging.exists():
            shutil.rmtree(staging)

