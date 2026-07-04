import os
import asyncio
import logging
from datetime import datetime, timezone
from celery import Celery, group, chord
from celery.signals import worker_ready, worker_shutdown

logger = logging.getLogger(__name__)

broker = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

app = Celery("scrapycoco", broker=broker, backend=backend)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,
    task_time_limit=600,
    beat_schedule={
        "cleanup-old-logs": {
            "task": "tasks.cleanup_old_executions",
            "schedule": 86400.0,
        },
        "quality-check-hourly": {
            "task": "tasks.run_quality_check",
            "schedule": 3600.0,
        },
    },
)


@worker_ready.connect
def on_worker_ready(**kwargs):
    logger.info("Celery worker ready")


@worker_shutdown.connect
def on_worker_shutdown(**kwargs):
    logger.info("Celery worker shutting down")


@app.task(bind=True, max_retries=3, default_retry_delay=60, name="tasks.run_scraper")
def run_scraper(self, scraper_id: str, sandbox: bool = False, **kwargs):
    from main import _run_single_scraper_internal
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            _run_single_scraper_internal(scraper_id, sandbox=sandbox, **kwargs)
        )
        return result
    except Exception as exc:
        logger.error(f"Task {scraper_id} failed: {exc}")
        raise self.retry(exc=exc)
    finally:
        loop.close()


@app.task(bind=True, max_retries=2, name="tasks.run_all_scrapers")
def run_all_scrapers(self, sandbox: bool = False):
    from main import SCRAPERS
    tasks = [run_scraper.s(sid, sandbox=sandbox) for sid in SCRAPERS]
    job = group(tasks)
    result = job.apply_async()
    return {"started": True, "task_count": len(tasks), "group_id": result.id}


@app.task(name="tasks.cleanup_old_executions")
def cleanup_old_executions(days: int = 30):
    from sqlalchemy import text
    from models.base import SessionLocal
    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc).isoformat()
        sql = "DELETE FROM execution_history WHERE started_at < :cutoff"
        db.execute(text(sql), {"cutoff": cutoff})
        db.commit()
        logger.info(f"Cleaned executions older than {days} days")
    finally:
        db.close()


@app.task(name="tasks.run_quality_check")
def run_quality_check():
    from pipeline_quality import quality_tracker
    report = quality_tracker.get_overall()
    logger.info(f"Quality check: score={report['overall_quality_score']}, items={report['total_items']}")
    return report


@app.task(name="tasks.clear_cache")
def clear_cache():
    from redis_client import get_client
    r = get_client()
    if r:
        import redis.asyncio as aioredis
        loop = asyncio.new_event_loop()
        loop.run_until_complete(r.flushdb())
        loop.close()
    return {"cleared": True}
