import re
from datetime import datetime

import scrapy


class FBrefSpider(scrapy.Spider):
    name = "fbref"
    allowed_domains = ["fbref.com"]
    custom_settings = {
        "DOWNLOAD_DELAY": 2.0,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
    }

    def __init__(self, seasons=None, leagues=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seasons = (seasons or "2025-2026").split(",")
        self.leagues = (leagues or "all").split(",")

    def start_requests(self):
        league_codes = {
            "EPL": "9", "La Liga": "12", "Serie A": "11",
            "Bundesliga": "20", "Ligue 1": "13", "all": None,
        }
        base_url = "https://fbref.com/en/comps/{code}/{season}/schedule/{season}-{slug}-Schedule"
        season_slugs = {
            "Premier League": "Premier-League", "La Liga": "La-Liga",
            "Serie A": "Serie-A", "Bundesliga": "Bundesliga",
            "Ligue 1": "Ligue-1",
        }

        for season in self.seasons:
            if self.leagues == ["all"]:
                for code, slug in [("9", "Premier-League"), ("12", "La-Liga"),
                                   ("11", "Serie-A"), ("20", "Bundesliga"),
                                   ("13", "Ligue-1")]:
                    url = f"https://fbref.com/en/comps/{code}/{season}/schedule/{season}-{slug}-Schedule"
                    yield scrapy.Request(url, callback=self.parse_schedule,
                                         meta={"season": season, "league_slug": slug})
            else:
                for league in self.leagues:
                    code = league_codes.get(league, "9")
                    slug = season_slugs.get(league, league.replace(" ", "-"))
                    url = f"https://fbref.com/en/comps/{code}/{season}/schedule/{season}-{slug}-Schedule"
                    yield scrapy.Request(url, callback=self.parse_schedule,
                                         meta={"season": season, "league_slug": slug})

    def parse_schedule(self, response):
        season = response.meta["season"]
        rows = response.css("table#sched_2025-2026_9_1 tbody tr") or response.css("table.stats_table tbody tr")
        for row in rows:
            if "thead" in row.attrib.get("class", ""):
                continue
            cells = row.css("td")
            if len(cells) < 10:
                continue
            match_data = self._extract_match(row, cells, season)
            if match_data:
                yield match_data

    def _extract_match(self, row, cells, season):
        try:
            home_raw = cells[3].css("a::text").get("").strip()
            away_raw = cells[6].css("a::text").get("").strip()
            score_text = cells[4].css("a::text").get("")
            date_text = cells[0].css("a::text").get("") or cells[0].css("::text").get("").strip()
            comp_text = cells[1].css("a::text").get("") or cells[1].css("::text").get("").strip()
            venue = cells[9].css("::text").get("").strip() if len(cells) > 9 else ""
            attendance = cells[10].css("::text").get("").strip() if len(cells) > 10 else ""
            referee = cells[11].css("::text").get("").strip() if len(cells) > 11 else ""

            home_goals, away_goals = None, None
            status = "scheduled"
            if score_text and "–" in score_text:
                parts = score_text.split("–")
                home_goals = int(parts[0].strip())
                away_goals = int(parts[1].strip())
                status = "completed"
            elif score_text and ":" in score_text:
                status = "live"

            yield {
                "source": self.name,
                "home_team": home_raw,
                "away_team": away_raw,
                "home_goals": home_goals,
                "away_goals": away_goals,
                "match_date": self._parse_fbref_date(date_text),
                "competition": comp_text,
                "season": season,
                "status": status,
                "venue": venue or None,
                "referee": referee or None,
                "attendance": self._parse_int(attendance),
            }

        except Exception as e:
            self.logger.warning(f"Failed to parse row: {e}")

    def _parse_fbref_date(self, text):
        text = re.sub(r"\s+", " ", text.strip())
        for fmt in ("%Y-%m-%d", "%d %b %Y", "%B %d, %Y"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None

    def _parse_int(self, text):
        text = re.sub(r"[^\d]", "", text)
        return int(text) if text else None
