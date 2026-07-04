import logging
from datetime import datetime

from scrapy_items import MatchItem, PlayerStatsItem, OddsItem, StandingItem, LineupItem
from models.base import SessionLocal
from models.match import Match
from models.player_stats import PlayerStats
from models.odds import Odds
from models.standing import Standing
from models.lineup import Lineup
from pipeline_orchestrator import run_pipeline

logger = logging.getLogger(__name__)

ITEM_TYPE_MAP = {
    MatchItem: "match",
    PlayerStatsItem: "player_stats",
    OddsItem: "odds",
    StandingItem: "standing",
    LineupItem: "lineup",
}


class DatabasePipeline:
    def __init__(self):
        self._buffer = {t: [] for t in ITEM_TYPE_MAP.values()}
        self.session = None

    def open_spider(self, **kwargs):
        self.session = SessionLocal()
        self.items_processed = 0

    def close_spider(self, **kwargs):
        self._flush_all()
        if self.items_processed > 0:
            self.session.commit()
        self.session.close()

    def process_item(self, item, **kwargs):
        item_type = ITEM_TYPE_MAP.get(type(item))
        if not item_type:
            return item

        item_dict = dict(item)
        self._buffer.setdefault(item_type, []).append(item_dict)

        if len(self._buffer[item_type]) >= 50:
            self._flush(item_type)

        self.items_processed += 1
        return item

    def _flush(self, item_type):
        items = self._buffer.get(item_type, [])
        if not items:
            return

        items, result = run_pipeline(item_type, items, track_quality=False)

        source_map = {t: s for s, t in ITEM_TYPE_MAP.items()}
        for item_dict in items:
            source = item_dict.pop("source", "scrapy")
            match_id = item_dict.pop("match_id", None)
            self._store(item_type, item_dict, source, match_id)

        self._buffer[item_type] = []

        if self.items_processed > 0 and self.items_processed % 200 == 0:
            self.session.commit()

    def _flush_all(self):
        for item_type in list(self._buffer.keys()):
            self._flush(item_type)

    def _store(self, item_type, data, source, match_id):
        try:
            if item_type == "match":
                self._process_match(data, source)
            elif item_type == "player_stats":
                self._process_player_stats(data, source, match_id)
            elif item_type == "odds":
                self._process_odds(data, source, match_id)
            elif item_type == "standing":
                self._process_standing(data, source)
            elif item_type == "lineup":
                self._process_lineup(data, source, match_id)
        except Exception as e:
            logger.error(f"Error storing {item_type}: {e}")
            self.session.rollback()

    def _parse_date(self, value):
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%d %b %Y"):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return None

    def _process_match(self, data, source):
        m = Match(
            source=source,
            home_team=data.get("home_team"),
            away_team=data.get("away_team"),
            home_goals=data.get("home_goals"),
            away_goals=data.get("away_goals"),
            match_date=self._parse_date(data.get("match_date")),
            competition=data.get("competition"),
            season=data.get("season"),
            status=data.get("status", "scheduled"),
            venue=data.get("venue"),
            referee=data.get("referee"),
            attendance=data.get("attendance"),
        )
        self.session.add(m)

    def _process_player_stats(self, data, source, match_id):
        s = PlayerStats(
            source=source, match_id=match_id,
            team=data.get("team"), player_name=data.get("player_name"),
            nationality=data.get("nationality"), position=data.get("position"),
            minutes_played=data.get("minutes_played"), goals=data.get("goals"),
            assists=data.get("assists"), shots=data.get("shots"),
            shots_on_target=data.get("shots_on_target"), xg=data.get("xg"),
            xa=data.get("xa"), key_passes=data.get("key_passes"),
            passes_attempted=data.get("passes_attempted"),
            passes_completed=data.get("passes_completed"),
            tackles=data.get("tackles"), interceptions=data.get("interceptions"),
            fouls=data.get("fouls"), yellow_card=data.get("yellow_card"),
            red_card=data.get("red_card"), rating=data.get("rating"),
        )
        self.session.add(s)

    def _process_odds(self, data, source, match_id):
        o = Odds(
            source=source, match_id=match_id,
            bookmaker=data.get("bookmaker", source),
            home_odd=data.get("home_odd"), draw_odd=data.get("draw_odd"),
            away_odd=data.get("away_odd"),
            over_under_line=data.get("over_under_line"),
            over_odd=data.get("over_odd"), under_odd=data.get("under_odd"),
            btts_yes=data.get("btts_yes"), btts_no=data.get("btts_no"),
            asian_handicap_line=data.get("asian_handicap_line"),
            asian_handicap_home=data.get("asian_handicap_home"),
            asian_handicap_away=data.get("asian_handicap_away"),
        )
        self.session.add(o)

    def _process_standing(self, data, source):
        s = Standing(
            source=source, competition=data.get("competition"),
            season=data.get("season"), position=data.get("position"),
            team=data.get("team"), played=data.get("played"),
            won=data.get("won"), drawn=data.get("drawn"),
            lost=data.get("lost"), goals_for=data.get("goals_for"),
            goals_against=data.get("goals_against"),
            goal_diff=data.get("goal_diff"), points=data.get("points"),
            form=data.get("form"),
        )
        self.session.add(s)

    def _process_lineup(self, data, source, match_id):
        l = Lineup(
            source=source, match_id=match_id, team=data.get("team"),
            formation=data.get("formation"), player_name=data.get("player_name"),
            shirt_number=data.get("shirt_number"),
            is_substitute=data.get("is_substitute", False),
            position=data.get("position"), captain=data.get("captain", False),
        )
        self.session.add(l)
