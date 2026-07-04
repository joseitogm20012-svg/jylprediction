from sqlalchemy import Column, Integer, String, Text, Float, Boolean
from models.base import Base


class ScrapingJob(Base):
    __tablename__ = "scraping_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scraper_id = Column(String(64), nullable=False, index=True)
    source = Column(String(64), nullable=False)
    status = Column(String(16), nullable=False, default="pending")
    worker_id = Column(String(64), nullable=True)
    progress = Column(Float, default=0.0)
    total_items = Column(Integer, nullable=True)
    processed_items = Column(Integer, nullable=True)
    error_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(String(32), nullable=True)
    finished_at = Column(String(32), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    sandbox = Column(Boolean, default=False)
    params = Column(Text, nullable=True)
    logs = Column(Text, nullable=True)
    celery_task_id = Column(String(64), nullable=True, unique=True)

    def __repr__(self):
        return f"<ScrapingJob {self.scraper_id} [{self.status}]>"
