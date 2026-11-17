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
Set `REPOMATCH_DATASET` in the root `.env` file to use another JSONL dataset:

```dotenv
REPOMATCH_DATASET=data/repositories.jsonl
```

Relative dataset paths start from the directory where you launch the API.
Restart the API after changing the dataset. Terminal environment variables take
precedence over `.env` values.

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








## Login and Signup

RepoMatch uses FastAPI, SQLite, and JWT for user authentication.

- Users can sign up and log in with an email and password.
- Passwords are securely hashed.
- Each user has a unique ID.

## Setup

**1. Install Python dependencies:**

```bash
python -m pip install -e .
```

**2. Create a `.env` file** in the main project folder.

Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Add it to `.env`:

```text
REPOMATCH_AUTH_SECRET=your_generated_key
```

**3. Start the backend:**

```bash
python -m repomatch.api
```

**4. Start the frontend in another terminal:**

```bash
cd frontend
npm install
npm run dev
```

**5. Open:** http://localhost:5173

Search immediately, or optionally create an account or log in.

## Database

User accounts are stored in `users.db`, which is automatically created by the backend.

Each developer has their own local database. The database and `.env` file are not uploaded to GitHub.
