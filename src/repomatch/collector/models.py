"""Shared helpers for the versioned repository record format.

A field's status describes collection, not project quality. In particular,
"missing" means we looked and did not find it; "failed" means we could not check.
"""

from datetime import datetime, timezone

SCHEMA_VERSION = 1
STATES = {"collected", "missing", "skipped", "failed"}
COLLECTION_FIELDS = ("languages", "readme", "contributing", "manifests", "listing")


def now() -> str:
    """Return an ISO timestamp with an explicit UTC offset."""
    return datetime.now(timezone.utc).isoformat()


def field_result(
    status: str,
    *,
    data=None,
    path=None,
    reason=None,
    sha=None,
    size=None,
) -> dict:
    """Build a field result, omitting optional values that were not supplied."""
    if status not in STATES:
        raise ValueError("Unknown collection status")

    result = {"status": status}
    optional_values = {
        "data": data,
        "path": path,
        "reason": reason,
        "sha": sha,
        "size": size,
    }
    for key, value in optional_values.items():
        if value is not None:
            result[key] = value

    return result


def validate_record(record: dict) -> dict:
    """Check the record's required identity, metadata, and collection states."""
    if record.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported record schema")

    repository_id = record.get("id")
    # bool is a subclass of int, but True is not a valid repository ID.
    if type(repository_id) is not int or repository_id <= 0:
        raise ValueError("Invalid repository ID")

    full_name = record.get("full_name")
    if not isinstance(full_name, str) or "/" not in full_name:
        raise ValueError("Invalid repository name")

    if not record.get("collected_at") or not isinstance(record.get("metadata"), dict):
        raise ValueError("Missing repository metadata")

    for name in COLLECTION_FIELDS:
        result = record.get(name, {})
        if result.get("status") not in STATES:
            raise ValueError(f"Invalid {name} state")

    manifests = record["manifests"]
    if manifests["status"] == "collected":
        for manifest in manifests["data"]:
            if manifest.get("status") not in STATES:
                raise ValueError("Invalid manifest state")

    return record


def has_failures(record: dict) -> bool:
    """Include individual manifest failures when deciding whether to retry."""
    for name in COLLECTION_FIELDS:
        if record[name]["status"] == "failed":
            return True

    for manifest in record["manifests"].get("data", []):
        if manifest["status"] == "failed":
            return True

    return False

