from sqlalchemy import Column, Integer, String, Text, Boolean
from models.base import Base


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scraper_id = Column(String(64), nullable=False, index=True)
    cron_expression = Column(String(64), nullable=False)
    params = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(String(32), nullable=False)
    last_run_at = Column(String(32), nullable=True)

    def __repr__(self):
        return f"<Schedule {self.scraper_id} [{self.cron_expression}]>"
