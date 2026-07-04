import re
from datetime import datetime

import scrapy
from scrapy_playwright.page import PageMethod


class FlashscoreSpider(scrapy.Spider):
    name = "flashscore"
    allowed_domains = ["flashscore.com", "flashscore.mobi", "flashscore.com.co"]
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "CONCURRENT_REQUESTS": 2,
    }

    def __init__(self, leagues=None, days=3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.leagues = (leagues or "all").split(",")
        self.days = int(days)

    def start_requests(self):
        url = "https://www.flashscore.com/football/"
        yield scrapy.Request(
            url,
            meta=dict(
                playwright=True,
                playwright_include_page=True,
                playwright_page_methods=[
                    PageMethod("wait_for_selector", "div[class*='event__match']", timeout=15000),
                    PageMethod("wait_for_timeout", 2000),
                ],
            ),
            callback=self.parse,
        )

    async def parse(self, response):
        page = response.meta["playwright_page"]
        try:
            html = await page.content()
            await page.close()
        except Exception:
            html = response.text

        selector = scrapy.Selector(text=html)
        for match_div in selector.css("div[class*='event__match']"):
            yield self._extract_match(match_div)

    def _extract_match(self, el):
        home = el.css("div[class*='event__homeParticipant']::text").get("").strip()
        away = el.css("div[class*='event__awayParticipant']::text").get("").strip()
        score_text = el.css("div[class*='event__score'] span::text").get("")
        date_text = el.css("div[class*='event__time']::text").get("")
        stage = el.css("div[class*='event__stage']::text").get("")
        league = el.css("div[class*='event__tournament']::text").get("")

        home_goals, away_goals = None, None
        status = "scheduled"
        if score_text and ":" in score_text:
            parts = score_text.split(":")
            home_goals = int(parts[0].strip()) if parts[0].strip().isdigit() else None
            away_goals = int(parts[1].strip()) if len(parts) > 1 and parts[1].strip().isdigit() else None
            if home_goals is not None and away_goals is not None:
                status = "live" if "live" in el.attrib.get("class", "").lower() else "completed"

        yield {
            "source": self.name,
            "home_team": home,
            "away_team": away,
            "home_goals": home_goals,
            "away_goals": away_goals,
            "match_date": self._parse_flash_date(date_text),
            "competition": league or stage or "",
            "season": self._infer_season(),
            "status": status,
        }

    def _parse_flash_date(self, text):
        if not text:
            return None
        text = text.strip()
        if text.isdigit() and len(text) == 10:
            return datetime.fromtimestamp(int(text))
        for fmt in ("%d.%m.%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None

    def _infer_season(self):
        now = datetime.now()
        year = now.year
        month = now.month
        if month >= 7:
            return f"{year}-{year + 1}"
        return f"{year - 1}-{year}"
