from sqlalchemy import Column, Integer, String, Float, Text, Index
from models.base import Base


class Odds(Base):
    __tablename__ = "odds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, nullable=False, index=True)
    bookmaker = Column(String(64), nullable=False)
    odd_home = Column(Float, nullable=True)
    odd_draw = Column(Float, nullable=True)
    odd_away = Column(Float, nullable=True)
    over_under_line = Column(Float, nullable=True)
    over_odds = Column(Float, nullable=True)
    under_odds = Column(Float, nullable=True)
    asian_handicap_line = Column(Float, nullable=True)
    asian_home_odds = Column(Float, nullable=True)
    asian_away_odds = Column(Float, nullable=True)
    btts_yes = Column(Float, nullable=True)
    btts_no = Column(Float, nullable=True)
    source = Column(String(32), default="oddspotal")
    recorded_at = Column(String(32), nullable=False)

    __table_args__ = (
        Index("ix_odds_match_bookmaker", "match_id", "bookmaker"),
    )

    def __repr__(self):
        return f"<Odds {self.bookmaker} [{self.odd_home}/{self.odd_draw}/{self.odd_away}]>"
