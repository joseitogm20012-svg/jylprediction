import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Any

DB_PATH = Path(__file__).parent / "scrapycoco.db"


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS execution_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scraper_id TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            duration_ms INTEGER,
            records_count INTEGER,
            error_message TEXT,
            sandbox INTEGER DEFAULT 0,
            metadata TEXT
        );
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scraper_id TEXT NOT NULL,
            cron_expression TEXT NOT NULL,
            params TEXT,
            enabled INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            last_run_at TEXT
        );
        CREATE TABLE IF NOT EXISTS credentials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT NOT NULL UNIQUE,
            encrypted_key TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS structure_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scraper_id TEXT NOT NULL,
            url TEXT DEFAULT '',
            snapshot TEXT NOT NULL,
            html_hash TEXT,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


def save_execution(
    scraper_id: str,
    status: str,
    started_at: str,
    finished_at: Optional[str] = None,
    duration_ms: Optional[int] = None,
    records_count: Optional[int] = None,
    error_message: Optional[str] = None,
    sandbox: bool = False,
    metadata: Optional[dict] = None
):
    conn = get_conn()
    conn.execute(
        """INSERT INTO execution_history
           (scraper_id, status, started_at, finished_at, duration_ms, records_count, error_message, sandbox, metadata)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (scraper_id, status, started_at, finished_at, duration_ms, records_count, error_message, 1 if sandbox else 0, json.dumps(metadata, ensure_ascii=False) if metadata else None)
    )
    conn.commit()
    conn.close()


def get_history(scraper_id: Optional[str] = None, limit: int = 100, offset: int = 0):
    conn = get_conn()
    cols = "id, scraper_id, status, started_at, finished_at, duration_ms, COALESCE(records_count, 0) as records_count, error_message, sandbox, metadata"
    if scraper_id:
        rows = conn.execute(
            f"SELECT {cols} FROM execution_history WHERE scraper_id=? ORDER BY started_at DESC LIMIT ? OFFSET ?",
            (scraper_id, limit, offset)
        ).fetchall()
    else:
        rows = conn.execute(
            f"SELECT {cols} FROM execution_history ORDER BY started_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if "sandbox" in d and d["sandbox"] is not None:
            d["sandbox"] = bool(d["sandbox"])
        if d.get("metadata"):
            try:
                d["metadata"] = json.loads(d["metadata"])
            except (json.JSONDecodeError, TypeError):
                pass
        result.append(d)
    return result


def get_metrics(scraper_id: Optional[str] = None):
    conn = get_conn()
    if scraper_id:
        row = conn.execute("""
            SELECT
                COUNT(*) as total_runs,
                SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) as error_count,
                AVG(CASE WHEN duration_ms IS NOT NULL THEN duration_ms ELSE NULL END) as avg_duration_ms,
                SUM(CASE WHEN records_count IS NOT NULL THEN records_count ELSE 0 END) as total_records,
                MIN(started_at) as first_run,
                MAX(started_at) as last_run
            FROM execution_history WHERE scraper_id=?
        """, (scraper_id,)).fetchone()
    else:
        row = conn.execute("""
            SELECT
                COUNT(*) as total_runs,
                SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) as error_count,
                AVG(CASE WHEN duration_ms IS NOT NULL THEN duration_ms ELSE NULL END) as avg_duration_ms,
                SUM(CASE WHEN records_count IS NOT NULL THEN records_count ELSE 0 END) as total_records,
                MIN(started_at) as first_run,
                MAX(started_at) as last_run
            FROM execution_history
        """).fetchone()
    conn.close()
    return dict(row) if row else {}


def save_snapshot(scraper_id: str, snapshot_json: str, html_hash: str, url: str = ""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO structure_snapshots (scraper_id, url, snapshot, html_hash, created_at) VALUES (?, ?, ?, ?, ?)",
        (scraper_id, url, snapshot_json, html_hash, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    conn.close()


def get_snapshots(scraper_id: str, limit: int = 20):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM structure_snapshots WHERE scraper_id=? ORDER BY created_at DESC LIMIT ?",
        (scraper_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_snapshot(snapshot_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM structure_snapshots WHERE id=?", (snapshot_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_latest_snapshot(scraper_id: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM structure_snapshots WHERE scraper_id=? ORDER BY created_at DESC LIMIT 1",
        (scraper_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_history_stats(scraper_id: Optional[str] = None):
    """Returns per-scraper stats for the history tab (last 30 days)."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            scraper_id,
            COUNT(*) as total_runs,
            SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as success_count,
            SUM(CASE WHEN status='error' THEN 1 ELSE 0 END) as error_count,
            AVG(CASE WHEN duration_ms IS NOT NULL THEN duration_ms ELSE NULL END) as avg_duration_ms,
            SUM(CASE WHEN records_count IS NOT NULL THEN records_count ELSE 0 END) as total_records,
            MAX(started_at) as last_run
        FROM execution_history
        GROUP BY scraper_id
        ORDER BY last_run DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]
