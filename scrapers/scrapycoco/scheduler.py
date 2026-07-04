import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, Callable, Awaitable

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False

import db

scheduler = None
_job_registry = {}
_executor_func: Optional[Callable] = None


def set_executor(func: Callable[..., Awaitable[dict]]):
    global _executor_func
    _executor_func = func


def start_scheduler():
    global scheduler
    if not HAS_APSCHEDULER:
        return False
    if scheduler is None or not scheduler.running:
        scheduler = AsyncIOScheduler()
        scheduler.start()
        _load_jobs_from_db()
    return True


def stop_scheduler():
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        scheduler = None


def _load_jobs_from_db():
    if not HAS_APSCHEDULER:
        return
    conn = db.get_conn()
    rows = conn.execute("SELECT * FROM schedules WHERE enabled=1").fetchall()
    conn.close()
    for row in rows:
        r = dict(row)
        _schedule_job(r["id"], r["scraper_id"], r["cron_expression"], r.get("params"))


def _schedule_job(db_id: int, scraper_id: str, cron_expr: str, params_json: Optional[str]):
    if not HAS_APSCHEDULER or scheduler is None:
        return
    params = {}
    if params_json:
        try:
            params = json.loads(params_json)
        except (json.JSONDecodeError, TypeError):
            params = {}

    async def job_func():
        if not _executor_func:
            return
        started_at = datetime.now(timezone.utc).isoformat()
        result = await _executor_func(
            scraper_id=scraper_id,
            sandbox=params.get("sandbox", False),
            match_id=params.get("match_id"),
            team_name=params.get("team_name"),
            type=params.get("type")
        )

        conn = db.get_conn()
        conn.execute(
            "UPDATE schedules SET last_run_at=? WHERE id=?",
            (datetime.now(timezone.utc).isoformat(), db_id)
        )
        conn.commit()
        conn.close()

    try:
        trigger = CronTrigger.from_crontab(cron_expr)
    except (ValueError, TypeError) as e:
        return
    job = scheduler.add_job(job_func, trigger, id=f"job_{db_id}", replace_existing=True, misfire_grace_time=60)
    _job_registry[db_id] = job


def add_job(scraper_id: str, cron_expression: str, params: Optional[dict] = None) -> int:
    conn = db.get_conn()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO schedules (scraper_id, cron_expression, params, enabled, created_at) VALUES (?, ?, ?, 1, ?)",
        (scraper_id, cron_expression, json.dumps(params) if params else None, now)
    )
    conn.commit()
    db_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    if HAS_APSCHEDULER and scheduler:
        _schedule_job(db_id, scraper_id, cron_expression, json.dumps(params) if params else None)

    return db_id


def remove_job(job_id: int):
    conn = db.get_conn()
    conn.execute("DELETE FROM schedules WHERE id=?", (job_id,))
    conn.commit()
    conn.close()

    if HAS_APSCHEDULER and scheduler:
        job_key = f"job_{job_id}"
        if job_key in scheduler.get_jobs():
            try:
                scheduler.remove_job(job_key)
            except Exception:
                pass
        if job_id in _job_registry:
            del _job_registry[job_id]


def pause_job(job_id: int):
    conn = db.get_conn()
    conn.execute("UPDATE schedules SET enabled=0 WHERE id=?", (job_id,))
    conn.commit()
    conn.close()

    if HAS_APSCHEDULER and scheduler:
        job_key = f"job_{job_id}"
        try:
            scheduler.pause_job(job_key)
        except Exception:
            pass


def resume_job(job_id: int):
    conn = db.get_conn()
    row = conn.execute("SELECT * FROM schedules WHERE id=?", (job_id,)).fetchone()
    if row:
        r = dict(row)
        conn.execute("UPDATE schedules SET enabled=1 WHERE id=?", (job_id,))
        conn.commit()
        _schedule_job(job_id, r["scraper_id"], r["cron_expression"], r.get("params"))
    conn.close()


def list_jobs():
    conn = db.get_conn()
    rows = conn.execute("SELECT * FROM schedules ORDER BY created_at DESC").fetchall()
    conn.close()
    result = []
    for row in rows:
        r = dict(row)
        r["next_run_time"] = None
        if HAS_APSCHEDULER and scheduler:
            job_key = f"job_{r['id']}"
            try:
                job = scheduler.get_job(job_key)
                if job and job.next_run_time:
                    r["next_run_time"] = job.next_run_time.isoformat()
            except Exception:
                pass
        result.append(r)
    return result
