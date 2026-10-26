# Collector guide

Start with the [README](../README.md) for setup and the collection commands.
This guide explains the options and how collection works.

## How collection works

**Discovery finds candidates.** The default plan searches eight languages
(Python, JavaScript, TypeScript, Java, C++, C#, Go, and Rust) across three star
bands: 10-99, 100-999, and 1,000+. It aims for 125 repositories per group,
3,000 total, with recently updated results first. Forks, private, archived, and
disabled repositories are excluded.

Repositories are deduplicated by GitHub ID. If groups overlap or run short, the
collector continues searching the same groups to fill the remaining places.
GitHub makes at most 1,000 results accessible per query, so the collector can stop
below its target. This is a structured sample, not a random sample of GitHub.

**Enrichment collects content.** For each candidate, it fetches current metadata
and language statistics, resolves a source commit, and retrieves the README.
A recursive file listing locates a contribution guide and root or nested dependency
manifests. Source files are fetched at that commit without cloning the repository.

Both stages save results and progress in SQLite. Requests run sequentially with
one second between request starts by default. Temporary errors are retried; a
rate-limit wait longer than the configured maximum stops the run. Resume later
by rerunning the command.

## Command reference

Prefix each command below with `python -m repomatch`.

| Command | What it does |
| --- | --- |
| `collect discover` | Find candidates up to the configured total (default 3,000) |
| `collect discover --limit 100` | Find up to 100 total candidates, including existing ones |
| `collect enrich` | Collect all pending candidates; skip completed records |
| `collect enrich --limit 10` | Attempt at most 10 repositories this run |
| `collect enrich --retry-failed` | Process pending, partial, and failed repositories |
| `collect enrich --refresh` | Recollect every candidate, including completed records |
| `collect status` | Count repositories by collection status |
| `collect export --snapshot NAME` | Export complete and partial records to a new snapshot |
| `collect analyze --snapshot NAME` | Verify a snapshot and generate statistics and charts |
| `collect readable --snapshot NAME` | Generate or replace its formatted JSON copy |

Retry and refresh recollect the whole repository, including previously successful
fields. Refresh takes precedence if both flags are supplied. Export requires a
new snapshot name; analysis and readable-copy generation can be rerun.

## Configuration

Edit [configs/collection.toml](../configs/collection.toml) to change the target,
sampling groups, file limits, or request timing. No `--limit` is needed for the
full configured target.

The optional [contributor plan](../configs/contributor-pilot.toml) uses its own
SQLite database. It combines general searches with searches for repositories
having good-first-issue labels, sorts by stars, and requires nonzero size and a
push date of 2025-10-23 or later. These signals do not guarantee a suitable
contribution opportunity.

To use it, add this option to **discovery, enrichment, status, and export**:

```powershell
python -m repomatch collect discover --config configs/contributor-pilot.toml
```

Analysis and readable-copy generation use the snapshot, so they do not need the
configuration option. All commands accept `--root PATH` to set the project root;
otherwise, run from the repository root. Relative paths resolve against that root.

## Common problems

- **Token missing or rejected:** check `GITHUB_TOKEN` in the root `.env` file.
  A shell variable overrides the file, even if empty. To use `.env` instead, run
  `Remove-Item Env:GITHUB_TOKEN -ErrorAction SilentlyContinue` in PowerShell.
- **Interrupted collection:** rerun the command. Saved work is retained; an
  unfinished repository may need to be fetched again. Recorded partial or failed
  results require `--retry-failed`.
- **Snapshot already exists:** choose a new name, such as `checkpoint1-v2`.
- **Export has fewer records than discovery:** pending and failed repositories
  are excluded. Check `collect status` and retry before exporting.

Only discovery and enrichment need a token. Status, export, analysis, and readable
copies work offline.
