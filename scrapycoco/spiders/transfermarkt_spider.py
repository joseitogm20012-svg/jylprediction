import re
from datetime import datetime

import scrapy
from scrapy_playwright.page import PageMethod


class TransfermarktSpider(scrapy.Spider):
    name = "transfermarkt"
    allowed_domains = ["transfermarkt.com", "transfermarkt.es"]
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "DOWNLOAD_DELAY": 3.0,
        "CONCURRENT_REQUESTS": 1,
    }

    def __init__(self, leagues=None, season=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.leagues = (leagues or "all").split(",")
        self.season = season or self._infer_season()

    def _infer_season(self):
        now = datetime.now()
        year = now.year
        month = now.month
        if month >= 7:
            return f"{year}/{year + 1}"
        return f"{year - 1}/{year}"

    def start_requests(self):
        competition_ids = {
            "Bundesliga": "L1", "Premier League": "GB1", "La Liga": "ES1",
            "Serie A": "IT1", "Ligue 1": "FR1",
        }
        base_url = "https://www.transfermarkt.com/{slug}/startseite/wettbewerb/{code}/plus/?saison_id={saison}"

        if self.leagues == ["all"]:
            targets = [
                ("premier-league", "GB1"),
                ("laliga", "ES1"),
                ("serie-a", "IT1"),
                ("bundesliga", "L1"),
                ("ligue-1", "FR1"),
            ]
        else:
            targets = []
            for league in self.leagues:
                code = competition_ids.get(league)
                slug = league.lower().replace(" ", "-")
                if code:
                    targets.append((slug, code))

        saison = self.season.split("/")[0] if "/" in self.season else self.season.split("-")[0]
        for slug, code in targets:
            url = base_url.format(slug=slug, code=code, saison=saison)
            yield scrapy.Request(
                url,
                meta=dict(
                    playwright=True,
                    playwright_include_page=True,
                    playwright_page_methods=[
                        PageMethod("wait_for_selector", "table.items", timeout=20000),
                        PageMethod("wait_for_timeout", 2000),
                    ],
                ),
                callback=self.parse,
            )

    async def parse(self, response):
        page = response.meta.get("playwright_page")
        try:
            html = await page.content() if page else response.text
        except Exception:
            html = response.text
        finally:
            if page:
                await page.close()

        selector = scrapy.Selector(text=html)
        competition = selector.css("h1::text").get("").strip()

        for row in selector.css("table.items tbody tr:not(.bg_blau_20)"):
            yield self._extract_row(row, competition)

    def _extract_row(self, row, competition):
        cells = row.css("td")
        home_td = row.css("td:nth-child(3) a")
        away_td = row.css("td:nth-child(6) a")
        score_td = row.css("td:nth-child(5) a")
        date_td = row.css("td:nth-child(1)")

        home = home_td.css("::text").get("").strip()
        away = away_td.css("::text").get("").strip()
        score_text = score_td.css("::text").get("").strip()
        date_text = date_td.css("::text").get("").strip()

        home_goals, away_goals = None, None
        status = "scheduled"
        if score_text and ":" in score_text:
            parts = score_text.split(":")
            try:
                home_goals = int(parts[0].strip())
                if "(" in parts[1]:
                    parts[1] = parts[1].split("(")[0]
                away_goals = int(parts[1].strip())
                status = "completed"
            except ValueError:
                pass

        yield {
            "source": self.name,
            "home_team": home,
            "away_team": away,
            "home_goals": home_goals,
            "away_goals": away_goals,
            "match_date": self._parse_date(date_text),
            "competition": competition,
            "season": self.season.replace("/", "-"),
            "status": status,
        }

    def _parse_date(self, text):
        text = re.sub(r"\s+", " ", text.strip())
        for fmt in ("%b %d, %Y", "%d %b %Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None
