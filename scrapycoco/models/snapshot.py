from sqlalchemy import Column, Integer, String, Text
from models.base import Base


class StructureSnapshot(Base):
    __tablename__ = "structure_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scraper_id = Column(String(64), nullable=False, index=True)
    url = Column(String(512), default="")
    snapshot = Column(Text, nullable=False)
    html_hash = Column(String(32), nullable=True, index=True)
    created_at = Column(String(32), nullable=False)

    def __repr__(self):
        return f"<StructureSnapshot {self.scraper_id} [{self.html_hash}]>"
