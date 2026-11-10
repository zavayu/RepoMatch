"""Read, write, and verify repository snapshots."""

import hashlib
import json
from pathlib import Path


def write_records(records, path: Path) -> int:
    """Stream compact JSONL with one repository per line."""
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as output:
        for record in records:
            serialized = json.dumps(
                record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            output.write(serialized + "\n")
            count += 1
    return count


def read_records(path: Path):
    with path.open(encoding="utf-8") as source:
        for line in source:
            yield json.loads(line)


def file_checksum(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()
