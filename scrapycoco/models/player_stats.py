from sqlalchemy import Column, Integer, String, Float, Text, Index
from models.base import Base


class PlayerStats(Base):
    __tablename__ = "player_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, nullable=False, index=True)
    team = Column(String(128), nullable=False)
    player_name = Column(String(128), nullable=False, index=True)
    shirt_number = Column(Integer, nullable=True)
    position = Column(String(16), nullable=True)
    minutes_played = Column(Integer, nullable=True)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    xg = Column(Float, nullable=True)
    xa = Column(Float, nullable=True)
    shots = Column(Integer, nullable=True)
    shots_on_target = Column(Integer, nullable=True)
    passes_completed = Column(Integer, nullable=True)
    passes_attempted = Column(Integer, nullable=True)
    pass_accuracy = Column(Float, nullable=True)
    dribbles_successful = Column(Integer, nullable=True)
    tackles = Column(Integer, nullable=True)
    interceptions = Column(Integer, nullable=True)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    fouls_committed = Column(Integer, nullable=True)
    fouls_suffered = Column(Integer, nullable=True)
    rating = Column(Float, nullable=True)
    source = Column(String(32), nullable=False, default="fbref")
    metadata_json = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_player_stats_match", "match_id", "player_name"),
        Index("ix_player_stats_team", "team", "match_id"),
    )

    def __repr__(self):
        return f"<PlayerStats {self.player_name} [{self.goals}G/{self.assists}A]>"
