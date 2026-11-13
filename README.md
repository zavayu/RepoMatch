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

## Run the frontend

Install Node.js 22.13 or newer, then run:

```powershell
cd frontend
npm install
npm run dev
```

In a second terminal at the repository root, start the search API:

```powershell
.\.venv\Scripts\python.exe -m repomatch.api
```

Open the local URL printed by Vite. Search by project interests and optional
comma-separated skills. Choose relevance + skills or keyword-only matching, and
expand a result to inspect its ranking signals. The API uses the bundled dataset.
Set `REPOMATCH_DATASET` to another JSONL file before starting the API to use it.

Vite forwards `/api` requests to the Python server at `127.0.0.1:8000`.
Both servers must be running for search to work. This is a local development
setup; production hosting must also route `/api` requests to the Python service.

Run `npm run build` to type-check and create a production build.

## Collect a new dataset (optional)

Copy `.env.example` to `.env` and set `GITHUB_TOKEN` to your GitHub token.
Then collect a small sample and run the demo with it.

```powershell
python -m repomatch collect --snapshot new-sample --limit 30
python demo.py --dataset data/snapshots/new-sample/repos.jsonl
```
