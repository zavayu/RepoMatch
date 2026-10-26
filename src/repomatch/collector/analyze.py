"""Validate snapshots and summarize dataset coverage, size, and distribution."""

from collections import Counter
import html
import json
from pathlib import Path

from .dataset import file_checksum, read_records, snapshot_dataset
from .models import validate_record

COVERAGE_FIELDS = ("readme", "contributing", "manifests", "languages")


def star_bucket(stars: int) -> str:
    """Use the same popularity boundaries as the original checkpoint report."""
    if stars < 10:
        return "0-9"
    if stars < 100:
        return "10-99"
    if stars < 1000:
        return "100-999"
    return "1000+"


def readme_size_bucket(size: int) -> str:
    if size == 0:
        return "0"
    if size < 1000:
        return "1-999"
    if size < 10000:
        return "1000-9999"
    return "10000+"


def has_collected_content(field_name: str, result: dict) -> bool:
    """A manifests list counts as covered only if at least one file succeeded."""
    if field_name == "manifests":
        return any(
            manifest["status"] == "collected"
            for manifest in result.get("data", [])
        )
    return result["status"] == "collected" and bool(result.get("data"))


def bar_chart(path: Path, title: str, values: dict, label: str):
    """Write a small SVG chart without adding a plotting dependency."""
    items = list(values.items())
    height = 90 + len(items) * 30
    maximum = max(values.values(), default=1) or 1

    elements = [
        (
            '<svg xmlns="http://www.w3.org/2000/svg" width="800" '
            f'height="{height}" viewBox="0 0 800 {height}">'
        ),
        '<rect width="100%" height="100%" fill="white"/>',
        (
            '<text x="20" y="28" font-family="sans-serif" font-size="20">'
            f'{html.escape(title)}</text>'
        ),
        (
            '<text x="20" y="52" font-family="sans-serif" font-size="12">'
            f'{html.escape(label)}</text>'
        ),
    ]

    for index, (name, count) in enumerate(items):
        y = 72 + index * 30
        width = count / maximum * 430
        # Escape dataset labels before inserting them into SVG markup.
        safe_name = html.escape(str(name))
        elements.extend(
            [
                (
                    f'<text x="20" y="{y + 15}" font-family="sans-serif" '
                    f'font-size="13">{safe_name}</text>'
                ),
                (
                    f'<rect x="220" y="{y}" width="{width:.1f}" '
                    'height="20" fill="#2563eb"/>'
                ),
                (
                    f'<text x="{230 + width:.1f}" y="{y + 15}" '
                    f'font-family="sans-serif" font-size="12">{count}</text>'
                ),
            ]
        )

    elements.append("</svg>")
    path.write_text("\n".join(elements), encoding="utf-8")


def write_figures(output, languages, coverage, stars, readme_lengths, count):
    """Keep report presentation separate from dataset counting."""
    bar_chart(
        output / "languages.svg",
        "Primary language distribution",
        dict(languages.most_common(15)),
        "Repository count; top 15 languages",
    )
    bar_chart(
        output / "coverage.svg",
        "Collected, nonempty field coverage",
        dict(coverage),
        f"Repositories out of {count}; manifests = at least one collected file",
    )
    bar_chart(
        output / "popularity.svg",
        "Repository popularity",
        dict(stars),
        "Repository count by stars at collection",
    )
    bar_chart(
        output / "readme-lengths.svg",
        "README text size",
        dict(readme_lengths),
        "Repository count by UTF-8 bytes; 0 includes unavailable READMEs",
    )


def analyze_snapshot(source: Path, output: Path):
    """Read records and verify integrity before writing any report files."""
    manifest_path = source / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    dataset_path = snapshot_dataset(source, manifest)
    checksum_matches = file_checksum(dataset_path) == manifest["sha256"]
    if not checksum_matches:
        raise ValueError("Snapshot checksum or record count does not match manifest")

    count = 0
    byte_total = dataset_path.stat().st_size
    repository_ids = set()
    languages = Counter()
    coverage = Counter({name: 0 for name in COVERAGE_FIELDS})
    states = {name: Counter() for name in COVERAGE_FIELDS}
    stars = Counter({"0-9": 0, "10-99": 0, "100-999": 0, "1000+": 0})
    readme_lengths = Counter(
        {"0": 0, "1-999": 0, "1000-9999": 0, "10000+": 0}
    )

    for raw_record in read_records(dataset_path):
        record = validate_record(raw_record)
        repository_id = record["id"]
        if repository_id in repository_ids:
            raise ValueError("Duplicate repository ID in snapshot")
        repository_ids.add(repository_id)

        count += 1
        primary_language = record["metadata"].get("language") or "Unknown"
        languages[primary_language] += 1

        for field_name in COVERAGE_FIELDS:
            result = record[field_name]
            states[field_name][result["status"]] += 1
            if has_collected_content(field_name, result):
                coverage[field_name] += 1

        star_count = record["metadata"].get("stargazers_count") or 0
        stars[star_bucket(star_count)] += 1

        readme = record["readme"].get("data", "")
        readme_bytes = len(readme.encode("utf-8"))
        readme_lengths[readme_size_bucket(readme_bytes)] += 1

    count_matches = count == manifest["record_count"]
    if not checksum_matches or not count_matches:
        raise ValueError("Snapshot checksum or record count does not match manifest")

    # Guard the denominator for an externally supplied empty snapshot.
    denominator = max(count, 1)
    coverage_percent = {
        name: round(covered_count / denominator * 100, 2)
        for name, covered_count in coverage.items()
    }
    summary = {
        "record_count": count,
        "dataset_bytes": byte_total,
        "average_record_bytes": byte_total / denominator,
        "primary_languages": dict(languages.most_common()),
        "field_coverage_counts": dict(coverage),
        "field_coverage_percent": coverage_percent,
        "field_states": {
            name: dict(counts) for name, counts in states.items()
        },
        "star_buckets": dict(stars),
        "readme_bytes_buckets": dict(readme_lengths),
    }

    output.mkdir(parents=True, exist_ok=True)
    summary_path = output / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2) + "\n",
        encoding="utf-8",
    )
    write_figures(output, languages, coverage, stars, readme_lengths, count)
    return summary

