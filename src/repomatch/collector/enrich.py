"""Fetch repository evidence at one commit, keeping errors distinct from absence."""

import base64
import json
import logging
from pathlib import PurePosixPath
from urllib.parse import quote

from .github import GitHubError, RateLimitError
from .manifests import select_manifests
from .models import SCHEMA_VERSION, field_result, now

LOG = logging.getLogger(__name__)
CONTRIBUTION_NAMES = {
    "contributing", "contributing.md", "contributing.rst", "contributing.txt",
    "contributions", "contributions.md", "contributions.rst", "contributions.txt",
}
METADATA_FIELDS = (
    "description", "html_url", "topics", "language", "stargazers_count",
    "forks_count", "open_issues_count", "license", "archived", "fork",
    "disabled", "created_at", "updated_at", "pushed_at", "default_branch",
    "size", "homepage", "visibility",
)


def is_fatal_error(error: GitHubError) -> bool:
    return isinstance(error, RateLimitError) or error.status in {401, 403}


def failed_field(error: GitHubError) -> dict:
    """Authentication and exhausted limits stop the run; other fields can fail."""
    if is_fatal_error(error):
        raise error
    return field_result("failed", reason=str(error))


def decode_file(item: dict, cap: int) -> dict:
    """Accept only bounded, regular UTF-8 text files from GitHub."""
    path = item.get("path")
    size = item.get("size", 0)
    if size > cap:
        return field_result("skipped", path=path, size=size, reason="size_limit")
    if item.get("type") not in (None, "file"):
        return field_result("skipped", path=path, reason="not_a_regular_file")
    if item.get("encoding") != "base64":
        return field_result("skipped", path=path, reason="unsupported_encoding")

    try:
        encoded = "".join(item.get("content", "").split())
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) > cap:
            return field_result("skipped", path=path, size=len(raw), reason="size_limit")
        text = raw.decode("utf-8-sig")
        if "\x00" in text:
            return field_result("skipped", path=path, reason="binary_content")
    except (ValueError, UnicodeDecodeError):
        return field_result("failed", path=path, reason="invalid_base64_or_utf8")

    return field_result(
        "collected", data=text, path=path, sha=item.get("sha"), size=len(raw)
    )


def fetch_text(client, endpoint, commit_sha, cap) -> dict:
    try:
        item = client.get(endpoint, {"ref": commit_sha}, allow_missing=True)
    except GitHubError as error:
        return failed_field(error)
    if item is None:
        return field_result("missing")
    if not isinstance(item, dict):
        return field_result("skipped", reason="not_a_regular_file")
    return decode_file(item, cap)


def fetch_file(client, base, entry, commit_sha, cap) -> dict:
    path = entry["path"]
    size = entry.get("size")
    if size is not None and size > cap:
        return field_result("skipped", path=path, size=size, reason="size_limit")
    result = fetch_text(
        client, base + "/contents/" + quote(path, safe="/"), commit_sha, cap
    )
    result.setdefault("path", path)
    return result


def inspect_file_tree(client, base, tree_sha):
    """Use one inventory strategy; request failures are handled per repository."""
    tree = client.get(
        base + "/git/trees/" + quote(tree_sha, safe=""), {"recursive": "1"}
    )
    entries = []
    for item in tree["tree"]:
        if item.get("type") != "blob" or item.get("mode") not in {"100644", "100755"}:
            continue
        entries.append({
            "name": item["path"].rsplit("/", 1)[-1],
            "path": item["path"],
            "type": "file",
            "size": item.get("size"),
            "sha": item.get("sha"),
        })

    truncated = bool(tree.get("truncated"))
    details = {
        "scope": "recursive_tree",
        "tree_sha": tree_sha,
        "entry_count": len(tree["tree"]),
        "truncated": truncated,
        "complete": not truncated,
    }
    if truncated:
        listing = field_result("failed", data=details, reason="Recursive file tree is truncated")
    else:
        listing = field_result("collected", data=details)
    return entries, listing


def missing_content(listing_complete: bool) -> dict:
    if not listing_complete:
        return field_result("failed", reason="listing_incomplete")
    return field_result("missing", reason="not_found_in_scope")


def collect_guide(client, base, entries, commit_sha, config, listing_complete):
    guides = [
        entry for entry in entries
        if str(PurePosixPath(entry["path"]).parent) in {".", ".github", "docs"}
        and entry["name"].lower() in CONTRIBUTION_NAMES
    ]
    guides.sort(key=lambda entry: (entry["path"].count("/"), entry["path"].lower()))
    if not guides:
        return missing_content(listing_complete)
    return fetch_file(client, base, guides[0], commit_sha, config.max_file_bytes)


def collect_manifests(client, base, entries, commit_sha, config, listing_complete):
    candidates = select_manifests(entries)
    results = []
    attempts = 0
    for entry in candidates:
        path = entry["path"]
        size = entry.get("size")
        if size is not None and size > config.max_file_bytes:
            result = field_result("skipped", path=path, size=size, reason="size_limit")
        elif attempts >= config.max_manifests:
            result = field_result("skipped", path=path, reason="manifest_count_limit")
        else:
            attempts += 1
            result = fetch_file(client, base, entry, commit_sha, config.max_file_bytes)
        result["component_path"] = str(PurePosixPath(path).parent)
        results.append(result)

    collection = (
        field_result("collected", data=results)
        if results else missing_content(listing_complete)
    )
    collection["coverage"] = {
        "candidate_count": len(candidates),
        "download_attempts": attempts,
        "listing_complete": listing_complete,
        "selection_limited": any(item["status"] == "skipped" for item in results),
    }
    return collection


def enrich_one(client, candidate: dict, config) -> dict:
    base = "/repos/" + quote(candidate["full_name"], safe="/")
    metadata = client.get(base)
    if metadata["id"] != candidate["id"]:
        raise GitHubError("Repository name now refers to a different repository ID")
    if any(metadata.get(flag) for flag in ("private", "archived", "fork", "disabled")):
        raise GitHubError("Repository is no longer eligible")

    try:
        branch = quote(metadata["default_branch"], safe="")
        commit = client.get(base + "/commits/" + branch)
    except GitHubError as error:
        if error.status != 409:
            raise
        commit = None  # Empty Git repository.

    record = {
        "schema_version": SCHEMA_VERSION,
        "id": metadata["id"],
        "full_name": metadata["full_name"],
        "metadata": {name: metadata.get(name) for name in METADATA_FIELDS},
        "commit_sha": commit["sha"] if commit else None,
        "collected_at": now(),
    }
    try:
        record["languages"] = field_result("collected", data=client.get(base + "/languages"))
    except GitHubError as error:
        record["languages"] = failed_field(error)

    if commit is None:
        for name in ("readme", "contributing", "manifests", "listing"):
            record[name] = field_result("missing", reason="empty_repository")
        return record

    commit_sha = commit["sha"]
    record["readme"] = fetch_text(
        client, base + "/readme", commit_sha, config.max_file_bytes
    )
    entries, record["listing"] = inspect_file_tree(
        client, base, commit["commit"]["tree"]["sha"]
    )
    listing_complete = record["listing"]["data"]["complete"]
    record["contributing"] = collect_guide(
        client, base, entries, commit_sha, config, listing_complete
    )
    record["manifests"] = collect_manifests(
        client, base, entries, commit_sha, config, listing_complete
    )
    return record


def enrich(client, store, config, *, limit=None, retry_failed=False, refresh=False):
    processed = 0
    for row in store.pending(retry_failed=retry_failed, refresh=refresh, limit=limit):
        try:
            record = enrich_one(client, json.loads(row["candidate"]), config)
            store.save_record(record)
            processed += 1
            LOG.info("Collected %s", row["full_name"])
        except GitHubError as error:
            store.fail(row["id"], str(error))
            if is_fatal_error(error) or error.status is None:
                raise
            LOG.warning("Failed %s: %s", row["full_name"], error)
    return processed

