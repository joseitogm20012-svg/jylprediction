import json
from datetime import datetime

import scrapy


class SofascoreSpider(scrapy.Spider):
    name = "sofascore"
    allowed_domains = ["sofascore.com", "api.sofascore.com"]
    custom_settings = {
        "DEFAULT_REQUEST_HEADERS": {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
            "Origin": "https://www.sofascore.com",
            "Referer": "https://www.sofascore.com/",
        },
        "DOWNLOAD_DELAY": 1.0,
    }

    API_BASE = "https://api.sofascore.com/api/v1"

    def __init__(self, days=7, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.days = int(days)

    def start_requests(self):
        from datetime import timedelta
        today = datetime.now().strftime("%Y-%m-%d")
        past = (datetime.now() - timedelta(days=self.days)).strftime("%Y-%m-%d")
        url = f"{self.API_BASE}/sport/football/scheduled-events/{past}/{today}"
        yield scrapy.Request(url, callback=self.parse_event_list)

    def parse_event_list(self, response):
        data = response.json()
        for event in data.get("events", []):
            match_id = event.get("id")
            if not match_id:
                continue
            yield self._extract_event(event)

    def _extract_event(self, event):
        home = event.get("homeTeam", {})
        away = event.get("awayTeam", {})
        score = event.get("homeScore", {}) or {}
        away_score = event.get("awayScore", {}) or {}
        tournament = event.get("tournament", {}) or {}
        season = event.get("season", {}) or {}
        status = event.get("status", {}) or {}

        home_goals = score.get("current") or score.get("normaltime") or score.get("display")
        away_goals = away_score.get("current") or away_score.get("normaltime") or away_score.get("display")
        start_timestamp = event.get("startTimestamp")

        status_text = "scheduled"
        status_code = status.get("type")
        if status_code == "finished":
            status_text = "completed"
        elif status_code in ("inprogress", "live"):
            status_text = "live"
        elif status_code == "postponed":
            status_text = "postponed"

        yield {
            "source": self.name,
            "home_team": home.get("name"),
            "away_team": away.get("name"),
            "home_goals": home_goals,
            "away_goals": away_goals,
            "match_date": datetime.fromtimestamp(start_timestamp) if start_timestamp else None,
            "competition": tournament.get("name"),
            "season": season.get("name"),
            "status": status_text,
        }
