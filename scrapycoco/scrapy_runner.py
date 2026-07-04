import os
import sys
import json
import logging
from datetime import datetime

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

sys.path.insert(0, os.path.dirname(__file__))

logger = logging.getLogger(__name__)

SPIDER_REGISTRY = {}

def register_spider(name, spider_class):
    SPIDER_REGISTRY[name] = spider_class

from spiders.fbref_spider import FBrefSpider
from spiders.flashscore_spider import FlashscoreSpider
from spiders.transfermarkt_spider import TransfermarktSpider
from spiders.sofascore_spider import SofascoreSpider
from spiders.oddsportal_spider import OddsPortalSpider

register_spider("fbref", FBrefSpider)
register_spider("flashscore", FlashscoreSpider)
register_spider("transfermarkt", TransfermarktSpider)
register_spider("sofascore", SofascoreSpider)
register_spider("oddsportal", OddsPortalSpider)

def get_settings():
    settings = get_project_settings()
    overrides = {
        "BOT_NAME": "scrapycoco",
        "SPIDER_MODULES": ["spiders"],
        "NEWSPIDER_MODULE": "spiders",
        "ROBOTSTXT_OBEY": False,
        "CONCURRENT_REQUESTS": int(os.environ.get("SCRAPY_CONCURRENCY", 8)),
        "DOWNLOAD_DELAY": float(os.environ.get("SCRAPY_DELAY", 1.5)),
        "USER_AGENT": "ScrapyCoco/1.0",
        "COOKIES_ENABLED": True,
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 3,
        "DOWNLOAD_TIMEOUT": 30,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.0,
        "AUTOTHROTTLE_MAX_DELAY": 10.0,
        "LOG_LEVEL": os.environ.get("SCRAPY_LOG_LEVEL", "INFO"),
        "ITEM_PIPELINES": {
            "scrapy_pipelines.DatabasePipeline": 300,
        },
        "DOWNLOADER_MIDDLEWARES": {
            "scrapy_middlewares.RandomUserAgentMiddleware": 400,
            "scrapy_middlewares.ProxyRotationMiddleware": 500,
            "scrapy_middlewares.RateLimitMiddleware": 600,
        },
    }
    for k, v in overrides.items():
        settings.set(k, v)
    return settings


class ScrapyRunner:
    def __init__(self):
        self.results = {}

    def run_spider(self, spider_name, **kwargs):
        if spider_name not in SPIDER_REGISTRY:
            return {"error": f"Spider '{spider_name}' not found", "available": list(SPIDER_REGISTRY.keys())}

        spider_class = SPIDER_REGISTRY[spider_name]
        settings = get_settings()
        process = CrawlerProcess(settings)

        start = datetime.now()
        stats = {}

        def _collect_stats(**kwargs):
            nonlocal stats
            stats = kwargs.get("stats", {})

        crawler = process.create_crawler(spider_class)
        crawler.signals.connect(_collect_stats, signal=scrapy.signals.stats_spider_closed)

        process.crawl(crawler, **kwargs)
        process.start()

        elapsed = (datetime.now() - start).total_seconds()
        return {
            "spider": spider_name,
            "elapsed_seconds": elapsed,
            "pages_crawled": stats.get("downloader/response_count", 0),
            "items_scraped": stats.get("item_scraped_count", 0),
            "errors": stats.get("log_count/ERROR", 0),
        }

    def run_all(self, **kwargs):
        results = {}
        for name in SPIDER_REGISTRY:
            try:
                results[name] = self.run_spider(name, **kwargs)
            except Exception as e:
                results[name] = {"error": str(e)}
        self.results = results
        return results
