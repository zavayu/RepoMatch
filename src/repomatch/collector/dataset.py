"""Canonical JSONL snapshots and optional readable JSON copies."""

import hashlib
import json
import os
from pathlib import Path
import tempfile


def write_records(records, path: Path) -> int:
    """Stream compact JSONL with one repository per line."""
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as output:
        for record in records:
            serialized = json.dumps(
                record,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            output.write(serialized + "\n")
            count += 1
    return count


def write_readable_records(records, path: Path) -> int:
    """Stream a pretty JSON array for manual inspection."""
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as output:
        output.write("[\n")
        for record in records:
            if count:
                output.write(",\n")

            serialized = json.dumps(
                record, ensure_ascii=False, sort_keys=True, indent=2
            )
            indented = "\n".join("  " + line for line in serialized.splitlines())
            output.write(indented)
            count += 1

        output.write("\n]\n")
    return count


def read_records(path: Path):
    """Stream canonical JSONL one repository at a time."""
    with path.open(encoding="utf-8") as source:
        for line in source:
            yield json.loads(line)


def file_checksum(path: Path) -> str:
    """Hash the stored bytes, including formatting, without loading the file."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def snapshot_dataset(snapshot: Path, manifest: dict) -> Path:
    """Resolve only known canonical filenames; never select a readable copy."""
    dataset_name = manifest.get("dataset_file", "repos.jsonl")
    if dataset_name != "repos.jsonl":
        raise ValueError("Unsupported dataset filename in manifest")
    return snapshot / dataset_name


def generate_readable_copy(snapshot: Path) -> dict:
    """Regenerate a derived copy without changing canonical data or metadata."""
    manifest_path = snapshot / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dataset = snapshot_dataset(snapshot, manifest)

    if file_checksum(dataset) != manifest["sha256"]:
        raise ValueError("Snapshot checksum does not match manifest")

    # Build beside the final copy, then replace it only after a successful write.
    # This preserves any existing readable copy if parsing or count checks fail.
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".readable-", suffix=".json", dir=snapshot
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    readable_path = snapshot / "repos.readable.json"
    try:
        count = write_readable_records(read_records(dataset), temporary_path)
        if count != manifest["record_count"]:
            raise ValueError("Snapshot record count does not match manifest")
        os.replace(temporary_path, readable_path)
    finally:
        temporary_path.unlink(missing_ok=True)

    return {"record_count": count, "readable_file": str(readable_path)}

