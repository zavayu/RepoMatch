# RepoMatch

RepoMatch will match developers with open source projects based on their skills,
experience, and interests. This repository currently implements the **GitHub data
collector**. Personalized search and the web app come later.

## Setup

Requires Python 3.12+. Run from the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

If you do not already have a `.env` file, create one

Open `.env` and replace the placeholder with your GitHub personal access token:

```dotenv
GITHUB_TOKEN=your-token
```

The token needs read access to public repository metadata and contents. The
collector loads it automatically. Do not commit your real token.

## Collect the dataset

Run these commands in order:

```powershell
# Find 3,000 repositories and save candidates in SQLite
python -m repomatch collect discover

# Fetch metadata, languages, READMEs, contribution guides, and dependency manifests
python -m repomatch collect enrich

# See how many repositories completed or need another attempt
python -m repomatch collect status

# Save collected records as a dataset
python -m repomatch collect export --snapshot checkpoint1

# Generate statistics and charts from that dataset
python -m repomatch collect analyze --snapshot checkpoint1
```

For a small test, use `collect discover --limit 100` in the first command.
The limit means **100 total candidates**, including any already stored. Without
it, discovery uses the configured target of 3,000. Check the reported counts:
discovery may find fewer candidates, and some repositories may fail enrichment.

Collection saves progress as it runs. After an interruption, rerun the same
command. To retry partial or failed repositories before exporting:

```powershell
python -m repomatch collect enrich --retry-failed
```

## Where the data goes

| Location | Contents |
| --- | --- |
| `data/working/collector.sqlite3` | Candidates, collected content, statuses, and resume progress |
| `data/snapshots/checkpoint1/repos.jsonl` | Exported dataset: one repository per line |
| `data/snapshots/checkpoint1/manifest.json` | Export settings, record count, and checksum |
| `reports/checkpoint1/` | Summary statistics and SVG charts |

README and manifest text live inside SQLite during collection; individual source
files are not saved to disk. Export includes complete and partial records.

A snapshot is a saved copy, not a live view of the database. To export again,
choose a new name and use it for subsequent commands.

For an easier-to-read JSON copy:

```powershell
python -m repomatch collect readable --snapshot checkpoint1
```

This creates `repos.readable.json` beside `repos.jsonl`. JSONL remains the main
dataset. Share snapshots with your teammate rather than the working database.

## More information

- [Collector guide](docs/collector.md): sampling, command options, and troubleshooting.
- [Dataset guide](docs/dataset.md): collected fields, file limits, and status meanings.

Run the offline tests with `python -m unittest discover -s tests -v`.
