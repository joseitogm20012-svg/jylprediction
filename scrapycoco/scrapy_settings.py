import os

BOT_NAME = "scrapycoco"

SPIDER_MODULES = ["spiders"]
NEWSPIDER_MODULE = "spiders"

USER_AGENT = "ScrapyCoco/1.0 (+https://github.com/jlypredictor/scrapycoco)"

ROBOTSTXT_OBEY = False
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 1.5
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS_PER_DOMAIN = 4

COOKIES_ENABLED = True
COOKIES_DEBUG = False

TELNETCONSOLE_ENABLED = False

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
}

SPIDER_MIDDLEWARES = {}

DOWNLOADER_MIDDLEWARES = {
    "scrapy_middlewares.RandomUserAgentMiddleware": 400,
    "scrapy_middlewares.ProxyRotationMiddleware": 500,
    "scrapy_middlewares.RateLimitMiddleware": 600,
    "scrapy_middlewares.CookieSessionMiddleware": 700,
}

ITEM_PIPELINES = {
    "scrapy_pipelines.DatabasePipeline": 300,
}

PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "timeout": 30000,
}
PLAYWRIGHT_CONTEXT_OPTIONS = {
    "viewport": {"width": 1366, "height": 768},
    "locale": "es-ES",
}

RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [429, 500, 502, 503, 504]

DOWNLOAD_TIMEOUT = 30

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

LOG_LEVEL = os.environ.get("SCRAPY_LOG_LEVEL", "INFO")
