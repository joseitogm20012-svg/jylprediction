import json
from datetime import datetime, timezone
from typing import Optional, Any

from sqlalchemy import text
from models.base import engine, init_db as sa_init_db, SessionLocal, get_database_url
from models.execution import ExecutionHistory
from models.schedule import Schedule
from models.credential import Credential
from models.snapshot import StructureSnapshot


def get_conn():
    return engine.connect()


def init_db():
    sa_init_db()


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
    db = SessionLocal()
    try:
        entry = ExecutionHistory(
            scraper_id=scraper_id,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            records_count=records_count,
            error_message=error_message,
            sandbox=sandbox,
            metadata_json=json.dumps(metadata, ensure_ascii=False) if metadata else None,
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()


def get_history(scraper_id: Optional[str] = None, limit: int = 100, offset: int = 0):
    db = SessionLocal()
    try:
        query = db.query(
            ExecutionHistory.id,
            ExecutionHistory.scraper_id,
            ExecutionHistory.status,
            ExecutionHistory.started_at,
            ExecutionHistory.finished_at,
            ExecutionHistory.duration_ms,
            ExecutionHistory.records_count,
            ExecutionHistory.error_message,
            ExecutionHistory.sandbox,
            ExecutionHistory.metadata_json,
        )
        if scraper_id:
            query = query.filter(ExecutionHistory.scraper_id == scraper_id)
        rows = query.order_by(ExecutionHistory.started_at.desc()).limit(limit).offset(offset).all()

        result = []
        for r in rows:
            d = {
                "id": r.id,
                "scraper_id": r.scraper_id,
                "status": r.status,
                "started_at": r.started_at,
                "finished_at": r.finished_at,
                "duration_ms": r.duration_ms,
                "records_count": r.records_count or 0,
                "error_message": r.error_message,
                "sandbox": bool(r.sandbox) if r.sandbox is not None else False,
            }
            if r.metadata_json:
                try:
                    d["metadata"] = json.loads(r.metadata_json)
                except (json.JSONDecodeError, TypeError):
                    pass
            result.append(d)
        return result
    finally:
        db.close()


def get_metrics(scraper_id: Optional[str] = None):
    db = SessionLocal()
    try:
        sql = """
            SELECT
                COUNT(*) as total_runs,
                COALESCE(SUM(CASE WHEN status='success' THEN 1 ELSE 0 END), 0) as success_count,
                COALESCE(SUM(CASE WHEN status='error' THEN 1 ELSE 0 END), 0) as error_count,
                AVG(CASE WHEN duration_ms IS NOT NULL THEN duration_ms ELSE NULL END) as avg_duration_ms,
                COALESCE(SUM(records_count), 0) as total_records,
                MIN(started_at) as first_run,
                MAX(started_at) as last_run
            FROM execution_history
        """
        params = {}
        if scraper_id:
            sql += " WHERE scraper_id = :sid"
            params["sid"] = scraper_id
        row = db.execute(text(sql), params).first()
        if row:
            return dict(row._mapping)
        return {}
    finally:
        db.close()


def get_history_stats(scraper_id: Optional[str] = None):
    db = SessionLocal()
    try:
        sql = """
            SELECT
                scraper_id,
                COUNT(*) as total_runs,
                COALESCE(SUM(CASE WHEN status='success' THEN 1 ELSE 0 END), 0) as success_count,
                COALESCE(SUM(CASE WHEN status='error' THEN 1 ELSE 0 END), 0) as error_count,
                AVG(CASE WHEN duration_ms IS NOT NULL THEN duration_ms ELSE NULL END) as avg_duration_ms,
                COALESCE(SUM(records_count), 0) as total_records,
                MAX(started_at) as last_run
            FROM execution_history
        """
        params = {}
        if scraper_id:
            sql += " WHERE scraper_id = :sid"
            params["sid"] = scraper_id
        sql += " GROUP BY scraper_id ORDER BY last_run DESC"
        rows = db.execute(text(sql), params).fetchall()
        return [dict(r._mapping) for r in rows]
    finally:
        db.close()


def save_snapshot(scraper_id: str, snapshot_json: str, html_hash: str, url: str = ""):
    db = SessionLocal()
    try:
        entry = StructureSnapshot(
            scraper_id=scraper_id,
            url=url,
            snapshot=snapshot_json,
            html_hash=html_hash,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        db.add(entry)
        db.commit()
    finally:
        db.close()


def get_snapshots(scraper_id: str, limit: int = 20):
    db = SessionLocal()
    try:
        rows = (
            db.query(StructureSnapshot)
            .filter(StructureSnapshot.scraper_id == scraper_id)
            .order_by(StructureSnapshot.created_at.desc())
            .limit(limit)
            .all()
        )
        return [dict(
            id=r.id,
            scraper_id=r.scraper_id,
            url=r.url,
            snapshot=r.snapshot,
            html_hash=r.html_hash,
            created_at=r.created_at,
        ) for r in rows]
    finally:
        db.close()


def get_snapshot(snapshot_id: int):
    db = SessionLocal()
    try:
        r = db.query(StructureSnapshot).filter(StructureSnapshot.id == snapshot_id).first()
        if r:
            return dict(
                id=r.id,
                scraper_id=r.scraper_id,
                url=r.url,
                snapshot=r.snapshot,
                html_hash=r.html_hash,
                created_at=r.created_at,
            )
        return None
    finally:
        db.close()


def get_latest_snapshot(scraper_id: str):
    db = SessionLocal()
    try:
        r = (
            db.query(StructureSnapshot)
            .filter(StructureSnapshot.scraper_id == scraper_id)
            .order_by(StructureSnapshot.created_at.desc())
            .first()
        )
        if r:
            return dict(
                id=r.id,
                scraper_id=r.scraper_id,
                url=r.url,
                snapshot=r.snapshot,
                html_hash=r.html_hash,
                created_at=r.created_at,
            )
        return None
    finally:
        db.close()
