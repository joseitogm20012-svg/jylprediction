from sqlalchemy import Column, Integer, String, Float, Date, Text, Index
from models.base import Base


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(64), nullable=True, unique=True, index=True)
    source = Column(String(32), nullable=False, default="manual")
    match_date = Column(Date, nullable=False, index=True)
    competition = Column(String(128), nullable=False, index=True)
    season = Column(String(16), nullable=True)
    round = Column(String(64), nullable=True)
    home_team = Column(String(128), nullable=False, index=True)
    away_team = Column(String(128), nullable=False, index=True)
    home_score = Column(Integer, nullable=True)
    away_score = Column(Integer, nullable=True)
    home_xg = Column(Float, nullable=True)
    away_xg = Column(Float, nullable=True)
    stadium = Column(String(256), nullable=True)
    attendance = Column(Integer, nullable=True)
    referee = Column(String(128), nullable=True)
    status = Column(String(16), default="scheduled")
    metadata_json = Column(Text, nullable=True)
    created_at = Column(String(32), nullable=False)
    updated_at = Column(String(32), nullable=True)

    __table_args__ = (
        Index("ix_matches_teams_date", "home_team", "away_team", "match_date"),
        Index("ix_matches_competition_season", "competition", "season"),
    )

    def __repr__(self):
        return f"<Match {self.home_team} vs {self.away_team} [{self.match_date}]>"
