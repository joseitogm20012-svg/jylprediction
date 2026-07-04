from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, Boolean
from models.base import Base


class ExecutionHistory(Base):
    __tablename__ = "execution_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scraper_id = Column(String(64), nullable=False, index=True)
    status = Column(String(16), nullable=False, default="running")
    started_at = Column(String(32), nullable=False)
    finished_at = Column(String(32), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    records_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    sandbox = Column(Boolean, default=False)
    metadata_json = Column("metadata", Text, nullable=True)

    def __repr__(self):
        return f"<ExecutionHistory {self.scraper_id} [{self.status}]>"
