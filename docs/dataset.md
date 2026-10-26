# Dataset guide

During collection, SQLite stores repository content and progress. Export produces
`repos.jsonl` (the main dataset) and `manifest.json` (settings, counts, timestamps,
size, and checksum). An optional `repos.readable.json` contains the same records
as a formatted JSON array. See the [README](../README.md) for commands and paths.

## What each repository contains

Records use schema version 1.

| Field | Contents |
| --- | --- |
| `id`, `full_name` | GitHub ID and `owner/name` |
| `metadata` | Description, URL, topics, primary language, stars, forks, open issue/PR count, license identification, dates, and other repository details |
| `languages` | Language names and byte counts |
| `readme` | Raw README text |
| `contributing` | One contribution guide from the root, `.github`, or `docs` |
| `manifests` | Dependency/build file contents, paths, component paths, and coverage information |
| `listing` | Whether the file inventory was complete |
| `commit_sha` | Source commit used for collected files; null for an empty repository |
| `discovered_at`, `collected_at` | UTC timestamps |
| `discovery` | Search names and queries that found the repository |
| `schema_version` | Record format version |

Metadata and language statistics are fetched live. README, guide, and manifest
contents use the same source commit within each record.

Manifests such as `package.json`, `pyproject.toml`, `Cargo.toml`, and `.csproj`
provide evidence for future framework and skill detection. The collector stores
this evidence; it does not yet infer frameworks. The full filename list is in
[manifests.py](../src/repomatch/collector/manifests.py).

## Collection limits

- At most **6 manifest download attempts per repository**.
- At most **100,000 bytes per text file**.
- Root and shallower manifests are preferred; documentation, examples, and tests
  have lower priority. Vendored and build directories are excluded.
- Only regular UTF-8 text files without NUL bytes are collected. Symlinks and
  submodules are not followed.

License identification is collected from metadata; license text is not downloaded.
Full source code, lockfiles, binaries, issue bodies, and user profiles are outside
the current collection scope.

## Understanding statuses

Repository statuses appear in `collect status`:

| Status | Meaning |
| --- | --- |
| `pending` | Discovered, awaiting enrichment |
| `complete` | Collection finished within its scope and limits |
| `partial` | A record was saved, but some collection failed or the file listing was truncated |
| `failed` | Enrichment could not finish successfully |

**Complete does not mean every relevant file was collected.** Missing files and
configured skips alone do not make a repository partial.

Inside a record, each content field has a `status`: `collected`, `missing`,
`skipped`, or `failed`. Successful content is in `data`; file results retain their
`path`, and successful files include `sha` and byte `size`. A `reason` explains
unavailable content when supplied.

Manifest coverage records how many candidates were found and downloads attempted,
whether the listing was complete, and whether selection was limited. A truncated
listing produces a partial record. A failed listing request marks the repository
failed for retry.

## Exports and reports

Export includes **complete and partial** records, ordered by GitHub ID. Pending
and failed records are excluded, but their counts appear in `manifest.json`.
If a refresh fails, its older record is also excluded until collection succeeds.

Analysis verifies the dataset checksum and record count, then writes:

| Output | Contents |
| --- | --- |
| `summary.json` | Counts, dataset size, languages, field coverage and statuses, star bands, and README sizes |
| `languages.svg` | Primary language distribution |
| `coverage.svg` | Repositories with collected, nonempty content |
| `popularity.svg` | Repository counts by star band |
| `readme-lengths.svg` | Repository counts by README byte size |

Manifest coverage means **at least one manifest was collected**, not that every
component was found. The zero-size README bucket includes unavailable and empty
READMEs; use field statuses to distinguish them.
