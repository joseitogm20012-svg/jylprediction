import re
from datetime import datetime

import scrapy
from scrapy_playwright.page import PageMethod


class OddsPortalSpider(scrapy.Spider):
    name = "oddsportal"
    allowed_domains = ["oddsportal.com"]
    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True},
        "DOWNLOAD_DELAY": 3.0,
        "CONCURRENT_REQUESTS": 1,
    }

    def __init__(self, leagues=None, days=3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.leagues = (leagues or "all").split(",")
        self.days = int(days)

    def start_requests(self):
        url = "https://www.oddsportal.com/football/"
        yield scrapy.Request(
            url,
            meta=dict(
                playwright=True,
                playwright_include_page=True,
                playwright_page_methods=[
                    PageMethod("wait_for_selector", "table.table-main", timeout=20000),
                    PageMethod("wait_for_timeout", 3000),
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

        sel = scrapy.Selector(text=html)
        for row in sel.css("table.table-main tbody tr"):
            yield self._extract_odds(row)

    def _extract_odds(self, row):
        home = row.css("td:nth-child(2)::text").get("").strip()
        away = row.css("td:nth-child(3)::text").get("").strip()
        odds_cells = row.css("td.odds-now")
        home_odd = self._parse_odd(odds_cells[0]) if odds_cells else None
        draw_odd = self._parse_odd(odds_cells[1]) if len(odds_cells) > 1 else None
        away_odd = self._parse_odd(odds_cells[2]) if len(odds_cells) > 2 else None
        date_text = row.css("td.date::text").get("").strip()

        if not home or not away:
            return None

        yield {
            "source": self.name,
            "home_team": home,
            "away_team": away,
            "home_odd": home_odd,
            "draw_odd": draw_odd,
            "away_odd": away_odd,
            "bookmaker": "oddsportal",
            "match_date": self._parse_date(date_text),
        }

    def _parse_odd(self, cell):
        text = cell.css("::text").get("").strip()
        try:
            return float(text)
        except ValueError:
            return None

    def _parse_date(self, text):
        if not text:
            return None
        for fmt in ("%Y-%m-%d", "%d %b %Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(text.strip(), fmt)
            except ValueError:
                continue
        return None
