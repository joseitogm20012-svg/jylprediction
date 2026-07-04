import hashlib
import json
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from models.base import SessionLocal


def _hash_row(row: dict, keys: list[str]) -> str:
    raw = "|".join(str(row.get(k, "")) for k in keys)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _timestamp():
    return datetime.utcnow().isoformat()


class DedupResult:
    def __init__(self):
        self.total = 0
        self.duplicates_removed = 0
        self.kept = 0
        self.kept_ids: list[int] = []

    @property
    def ratio(self):
        if self.total == 0:
            return 1.0
        return round(self.kept / self.total, 3)


def dedup_matches(rows: list[dict], session=None) -> tuple[list[dict], DedupResult]:
    """Dedup by (home_team, away_team, match_date) composite key."""
    result = DedupResult()
    result.total = len(rows)
    seen = set()
    kept = []

    for row in rows:
        h = row.get("home_team", "")
        a = row.get("away_team", "")
        d = str(row.get("match_date", ""))
        key = (h, a, d)
        if key not in seen:
            seen.add(key)
            kept.append(row)

    result.kept = len(kept)
    result.duplicates_removed = result.total - result.kept
    return kept, result


def dedup_player_stats(rows: list[dict]) -> tuple[list[dict], DedupResult]:
    """Dedup by (match_id, player_name, team)."""
    result = DedupResult()
    result.total = len(rows)
    seen = set()
    kept = []

    for row in rows:
        mid = row.get("match_id", "")
        pn = row.get("player_name", "")
        tm = row.get("team", "")
        key = (str(mid), str(pn), str(tm))
        if key not in seen:
            seen.add(key)
            kept.append(row)

    result.kept = len(kept)
    result.duplicates_removed = result.total - result.kept
    return kept, result


def dedup_odds(rows: list[dict]) -> tuple[list[dict], DedupResult]:
    """Dedup by (match_id, bookmaker)."""
    result = DedupResult()
    result.total = len(rows)
    seen = set()
    kept = []

    for row in rows:
        mid = row.get("match_id", "")
        bm = row.get("bookmaker", "")
        key = (str(mid), str(bm))
        if key not in seen:
            seen.add(key)
            kept.append(row)

    result.kept = len(kept)
    result.duplicates_removed = result.total - result.kept
    return kept, result


def dedup_standings(rows: list[dict]) -> tuple[list[dict], DedupResult]:
    """Dedup by (competition, season, team)."""
    result = DedupResult()
    result.total = len(rows)
    seen = set()
    kept = []

    for row in rows:
        comp = row.get("competition", "")
        seas = row.get("season", "")
        tm = row.get("team", "")
        key = (str(comp), str(seas), str(tm))
        if key not in seen:
            seen.add(key)
            kept.append(row)

    result.kept = len(kept)
    result.duplicates_removed = result.total - result.kept
    return kept, result


DEDUP_REGISTRY = {
    "match": dedup_matches,
    "player_stats": dedup_player_stats,
    "odds": dedup_odds,
    "standing": dedup_standings,
}


def dedup(item_type: str, rows: list[dict]) -> tuple[list[dict], DedupResult]:
    fn = DEDUP_REGISTRY.get(item_type)
    if fn:
        return fn(rows)
    return rows, DedupResult()
