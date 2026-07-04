from sqlalchemy import Column, Integer, String, Boolean, Text, Index
from models.base import Base


class Lineup(Base):
    __tablename__ = "lineups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, nullable=False, index=True)
    team = Column(String(128), nullable=False)
    formation = Column(String(16), nullable=True)
    player_name = Column(String(128), nullable=False)
    shirt_number = Column(Integer, nullable=True)
    position = Column(String(16), nullable=True)
    is_starter = Column(Boolean, default=True)
    is_captain = Column(Boolean, default=False)
    is_keeper = Column(Boolean, default=False)
    played_minutes = Column(Integer, nullable=True)
    source = Column(String(32), default="flashscore")

    __table_args__ = (
        Index("ix_lineups_match_team", "match_id", "team"),
    )

    def __repr__(self):
        role = "CAP" if self.is_captain else ("GK" if self.is_keeper else "SUB" if not self.is_starter else "STA")
        return f"<Lineup {self.player_name} [{role}]>"
