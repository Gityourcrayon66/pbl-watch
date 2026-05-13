import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_hash TEXT UNIQUE NOT NULL,
    url TEXT NOT NULL,
    source TEXT NOT NULL,
    title TEXT,
    published TEXT,
    status TEXT NOT NULL DEFAULT 'discovered',
    summary_json TEXT,
    raw_text_excerpt TEXT,
    error TEXT,
    discovered_at TEXT NOT NULL,
    summarized_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_published ON documents(published);
"""


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Storage:
    def __init__(self, db_path: Path):
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        with self._conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def upsert_discovery(self, source, url, title, published) -> bool:
        h = url_hash(url)
        with self._conn() as c:
            if c.execute("SELECT 1 FROM documents WHERE url_hash = ?", (h,)).fetchone():
                return False
            c.execute(
                "INSERT INTO documents (url_hash, url, source, title, published, status, discovered_at)"
                " VALUES (?, ?, ?, ?, ?, 'discovered', ?)",
                (h, url, source, title, published, now_iso()),
            )
            return True

    def pending(self, limit: int):
        with self._conn() as c:
            cur = c.execute(
                "SELECT * FROM documents WHERE status = 'discovered' "
                "ORDER BY discovered_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]

    def save_summary(self, doc_id: int, summary: dict, excerpt: str):
        with self._conn() as c:
            c.execute(
                "UPDATE documents SET status='summarized', summary_json=?, "
                "raw_text_excerpt=?, summarized_at=? WHERE id=?",
                (json.dumps(summary, ensure_ascii=False), excerpt, now_iso(), doc_id),
            )

    def mark_failed(self, doc_id: int, error: str):
        with self._conn() as c:
            c.execute(
                "UPDATE documents SET status='failed', error=? WHERE id=?",
                (error[:500], doc_id),
            )

    def all_summarized(self):
        with self._conn() as c:
            cur = c.execute(
                "SELECT * FROM documents WHERE status='summarized' "
                "ORDER BY summarized_at DESC"
            )
            return [dict(r) for r in cur.fetchall()]

    def counts(self) -> dict:
        with self._conn() as c:
            cur = c.execute("SELECT status, COUNT(*) FROM documents GROUP BY status")
            return {row[0]: row[1] for row in cur.fetchall()}
