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



## Checkpoint 2: Recommendation Algorithm

RepoMatch recommends GitHub repositories based on user interests and programming skills.

### How It Works

1. **BM25 (35%):** Finds the top 30 repositories based on keyword relevance.
2. **TF-IDF (45%):** Uses cosine similarity to compare the user's query with repository text.
3. **Skill Matching (20%):** Compares user skills with repository technologies.

The algorithm combines these scores and returns the top 5 recommendations.

### How to Run

Install dependencies from the repository root:

```powershell
python -m pip install -e .
```

Make sure `data/repositories.jsonl` contains the sample dataset.

Run the demo:

```powershell
python demo.py
```

Enter a project query and comma-separated programming skills. The demo defaults
to the bundled 30-repository sample and returns up to five results.

If you have the full Checkpoint 1 JSONL snapshot locally, compare both modes
using the same query:

```powershell
python demo.py --dataset data/snapshots/checkpoint1/repos.jsonl --mode checkpoint2 --top 10 --debug
python demo.py --dataset data/snapshots/checkpoint1/repos.jsonl --mode bm25 --top 10 --debug
```

The BM25 baseline takes only the query and ranks by raw BM25. The debug view
shows normalized BM25 and the TF-IDF and skill scores used in Checkpoint 2.
TF-IDF and skill scores are zero in BM25 mode.

## More information

- [Collector guide](docs/collector.md): sampling, command options, and troubleshooting.
- [Dataset guide](docs/dataset.md): collected fields, file limits, and status meanings.

Run the offline tests with `python -m unittest discover -s tests -v`.
