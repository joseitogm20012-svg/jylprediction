from sqlalchemy import Column, Integer, String, Float, Index
from models.base import Base


class Standing(Base):
    __tablename__ = "standings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    competition = Column(String(128), nullable=False, index=True)
    season = Column(String(16), nullable=False)
    team = Column(String(128), nullable=False, index=True)
    position = Column(Integer, nullable=False)
    played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    goals_for = Column(Integer, default=0)
    goals_against = Column(Integer, default=0)
    goal_difference = Column(Integer, default=0)
    points = Column(Integer, default=0)
    form = Column(String(16), nullable=True)
    home_wins = Column(Integer, default=0)
    home_draws = Column(Integer, default=0)
    home_losses = Column(Integer, default=0)
    away_wins = Column(Integer, default=0)
    away_draws = Column(Integer, default=0)
    away_losses = Column(Integer, default=0)
    source = Column(String(32), default="livescore")
    last_updated = Column(String(32), nullable=False)

    __table_args__ = (
        Index("ix_standings_comp_season", "competition", "season"),
        Index("ix_standings_comp_pos", "competition", "season", "position"),
    )

    def __repr__(self):
        return f"<Standing #{self.position} {self.team} [{self.points}pts]>"
