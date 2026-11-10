# RepoMatch

## Set up

Install Python 3.12 or newer and run these commands from the repository root.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

On macOS or Linux, activate the environment with `source .venv/bin/activate`.

## Run the demo

```powershell
python demo.py
```

Enter the kind of project you want to find, such as `online book reader`.
Then enter comma-separated skills like `JavaScript, HTML`. Press Enter to skip
skills. The demo uses the bundled dataset and shows up to five matches.

## Collect a new dataset (optional)

Copy `.env.example` to `.env` and set `GITHUB_TOKEN` to your GitHub token.
Then collect a small sample and run the demo with it.

```powershell
python -m repomatch collect --snapshot new-sample --limit 30
python demo.py --dataset data/snapshots/new-sample/repos.jsonl
```
