"""Persist collection work in SQLite; share JSONL exports with teammates.

Repositories move from pending to complete, partial, or failed. Each update commits
independently, so an interrupted run can resume without losing finished work.
"""

import json
from pathlib import Path
import sqlite3

from .models import has_failures, now, validate_record


class Store:
    """Own the working database and the collector's progress queries."""

    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row

        # Provenance is separate because several searches can find the same ID.
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY,
                full_name TEXT NOT NULL,
                candidate TEXT NOT NULL,
                record TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                error TEXT,
                discovered_at TEXT NOT NULL,
                collected_at TEXT
            );
            CREATE TABLE IF NOT EXISTS provenance (
                repo_id INTEGER NOT NULL,
                search_name TEXT NOT NULL,
                query TEXT NOT NULL,
                PRIMARY KEY (repo_id, search_name, query)
            );
            CREATE TABLE IF NOT EXISTS search_progress (
                key TEXT PRIMARY KEY,
                page INTEGER NOT NULL DEFAULT 1,
                exhausted INTEGER NOT NULL DEFAULT 0,
                total_count INTEGER,
                incomplete INTEGER NOT NULL DEFAULT 0
            );
            """
        )

    def close(self):
        self.db.close()

    def count(self) -> int:
        """Count unique candidates, whether or not enrichment has finished."""
        row = self.db.execute("SELECT count(*) FROM repositories").fetchone()
        return row[0]

    def add(self, repo: dict, search):
        """Save a candidate and its source search without creating duplicate IDs."""
        with self.db:
            self.db.execute(
                """
                INSERT OR IGNORE INTO repositories
                    (id, full_name, candidate, discovered_at)
                VALUES (?, ?, ?, ?)
                """,
                (repo["id"], repo["full_name"], json.dumps(repo), now()),
            )
            self.db.execute(
                """
                INSERT OR IGNORE INTO provenance (repo_id, search_name, query)
                VALUES (?, ?, ?)
                """,
                (repo["id"], search.name, search.query),
            )

    def search_count(self, search) -> int:
        """Count this search's matches, including IDs found by other searches."""
        row = self.db.execute(
            """
            SELECT count(*) FROM provenance
            WHERE search_name = ? AND query = ?
            """,
            (search.name, search.query),
        ).fetchone()
        return row[0]

    def progress(self, key: str) -> dict:
        """Start unseen searches at page one."""
        row = self.db.execute(
            "SELECT * FROM search_progress WHERE key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return {"page": 1, "exhausted": 0}
        return dict(row)

    def save_progress(self, key, page, exhausted, total, incomplete):
        with self.db:
            self.db.execute(
                """
                INSERT OR REPLACE INTO search_progress
                    (key, page, exhausted, total_count, incomplete)
                VALUES (?, ?, ?, ?, ?)
                """,
                (key, page, int(exhausted), total, int(incomplete)),
            )

    def pending(self, retry_failed=False, refresh=False, limit=None):
        """Select work in ID order; refresh takes precedence over retry_failed."""
        if refresh:
            condition = ""
        elif retry_failed:
            condition = "WHERE status IN ('pending', 'partial', 'failed')"
        else:
            condition = "WHERE status = 'pending'"

        query = f"SELECT * FROM repositories {condition} ORDER BY id"
        parameters = ()
        if limit is not None:
            query += " LIMIT ?"
            parameters = (limit,)

        return self.db.execute(query, parameters).fetchall()

    def save_record(self, record: dict):
        """A partial record remains exportable, but is eligible for a retry."""
        validate_record(record)
        status = "partial" if has_failures(record) else "complete"

        with self.db:
            self.db.execute(
                """
                UPDATE repositories
                SET record = ?, status = ?, error = NULL, collected_at = ?
                WHERE id = ?
                """,
                (
                    json.dumps(record, ensure_ascii=False),
                    status,
                    record["collected_at"],
                    record["id"],
                ),
            )

    def fail(self, repo_id: int, error):
        """Keep the error for inspection and exclude stale data from exports."""
        with self.db:
            self.db.execute(
                "UPDATE repositories SET status = 'failed', error = ? WHERE id = ?",
                (str(error), repo_id),
            )

    def records(self):
        """Yield exportable records, with timestamps and discovery provenance."""
        rows = self.db.execute(
            """
            SELECT * FROM repositories
            WHERE record IS NOT NULL AND status IN ('complete', 'partial')
            ORDER BY id
            """
        )
        for row in rows:
            record = validate_record(json.loads(row["record"]))
            sources = self.db.execute(
                """
                SELECT search_name, query FROM provenance
                WHERE repo_id = ?
                ORDER BY search_name, query
                """,
                (row["id"],),
            )
            record["discovered_at"] = row["discovered_at"]
            record["discovery"] = [dict(source) for source in sources]
            yield record

    def stats(self) -> dict:
        rows = self.db.execute(
            "SELECT status, count(*) FROM repositories GROUP BY status"
        )
        return {row[0]: row[1] for row in rows}

