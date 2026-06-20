"""SQLite storage layer. One table, upsert by stable id."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import Resource

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "resources.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS resources (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    url         TEXT NOT NULL,
    description TEXT,
    type        TEXT,
    topics      TEXT,
    cost        TEXT,
    source      TEXT,
    provider    TEXT,
    found_at    TEXT,
    event_date  TEXT,
    status      TEXT,
    notes       TEXT
);
CREATE INDEX IF NOT EXISTS idx_type   ON resources(type);
CREATE INDEX IF NOT EXISTS idx_status ON resources(status);
"""

_COLS = [
    "id", "title", "url", "description", "type", "topics", "cost",
    "source", "provider", "found_at", "event_date", "status", "notes",
]


class Store:
    def __init__(self, path: Path | str = DEFAULT_DB):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)

    def upsert(self, r: Resource) -> bool:
        """Insert or update. Returns True if this id was new."""
        row = r.to_row()
        existed = self.conn.execute(
            "SELECT 1 FROM resources WHERE id = ?", (r.id,)
        ).fetchone()
        placeholders = ",".join("?" for _ in _COLS)
        updates = ",".join(f"{c}=excluded.{c}" for c in _COLS if c != "id")
        self.conn.execute(
            f"INSERT INTO resources ({','.join(_COLS)}) VALUES ({placeholders}) "
            f"ON CONFLICT(id) DO UPDATE SET {updates}",
            [row[c] for c in _COLS],
        )
        self.conn.commit()
        return existed is None

    def upsert_many(self, resources) -> int:
        """Returns the count of newly added (not previously seen) resources."""
        new = 0
        for r in resources:
            if self.upsert(r):
                new += 1
        return new

    def all(self, status: str | None = None) -> list[Resource]:
        q = "SELECT * FROM resources"
        params: list = []
        if status:
            q += " WHERE status = ?"
            params.append(status)
        q += " ORDER BY found_at DESC, title"
        rows = self.conn.execute(q, params).fetchall()
        return [Resource.from_row(dict(r)) for r in rows]

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]

    def close(self) -> None:
        self.conn.close()
