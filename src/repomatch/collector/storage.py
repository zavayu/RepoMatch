"""Save the candidate list and commit each repository as collection progresses."""

import json
from pathlib import Path
import sqlite3

from .models import has_failures, now, validate_record


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                search_name TEXT NOT NULL,
                query TEXT NOT NULL,
                discovered_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                record TEXT
            )
            """
        )

    def close(self):
        self.db.close()

    def count(self):
        return self.db.execute("SELECT count(*) FROM repositories").fetchone()[0]

    def pending_count(self):
        return self.db.execute(
            "SELECT count(*) FROM repositories WHERE status = 'pending'"
        ).fetchone()[0]

    def seed(self, candidates):
        """Save the whole candidate list once, even if two runs discover it."""
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            if self.count():
                return
            discovered_at = now()
            self.db.executemany(
                """
                INSERT INTO repositories (id, full_name, search_name, query, discovered_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    (repo["id"], repo["full_name"], search.name, search.query, discovered_at)
                    for repo, search in candidates
                ),
            )

    def pending(self):
        rows = self.db.execute(
            "SELECT id, full_name FROM repositories WHERE status = 'pending' ORDER BY id"
        )
        return [{"id": repo_id, "full_name": name} for repo_id, name in rows]

    def save(self, repo_id, record=None):
        status, payload = "failed", None
        if record is not None:
            validate_record(record)
            status = "partial" if has_failures(record) else "complete"
            payload = json.dumps(record, ensure_ascii=False)
        with self.db:
            self.db.execute(
                """
                UPDATE repositories SET status = ?, record = ?
                WHERE id = ? AND status = 'pending'
                """,
                (status, payload, repo_id),
            )

    def records(self):
        rows = self.db.execute(
            """
            SELECT record, search_name, query, discovered_at
            FROM repositories WHERE record IS NOT NULL ORDER BY id
            """
        )
        for record_json, search_name, query, discovered_at in rows:
            record = json.loads(record_json)
            record["discovered_at"] = discovered_at
            record["discovery"] = [{"search_name": search_name, "query": query}]
            yield record

    def stats(self):
        return dict(self.db.execute("SELECT status, count(*) FROM repositories GROUP BY status"))
