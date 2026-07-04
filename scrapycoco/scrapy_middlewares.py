import random
import time
from collections import defaultdict
from urllib.parse import urlparse

from scrapy import signals
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.utils.response import response_status_message


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.207 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
]

FINGERPRINT_HEADERS = [
    ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
    ("Accept-Language", "es-ES,es;q=0.9,en;q=0.8"),
    ("Accept-Encoding", "gzip, deflate, br"),
    ("Sec-Ch-Ua", '"Not/A)Brand";v="99", "Google Chrome";v="125", "Chromium";v="125"'),
    ("Sec-Ch-Ua-Mobile", "?0"),
    ("Sec-Ch-Ua-Platform", '"Windows"'),
    ("Sec-Fetch-Dest", "document"),
    ("Sec-Fetch-Mode", "navigate"),
    ("Sec-Fetch-Site", "none"),
    ("Sec-Fetch-User", "?1"),
    ("Upgrade-Insecure-Requests", "1"),
]


class RandomUserAgentMiddleware:
    def process_request(self, request, **kwargs):
        request.headers["User-Agent"] = random.choice(USER_AGENTS)
        for key, value in FINGERPRINT_HEADERS:
            if key not in request.headers:
                request.headers[key] = value


class ProxyRotationMiddleware:
    _proxies = []
    _index = 0

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        proxy_list = crawler.settings.get("PROXY_LIST", [])
        if proxy_list:
            middleware._proxies = proxy_list
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware

    def spider_opened(self, spider):
        spider.logger.info(f"Proxy middleware loaded with {len(self._proxies)} proxies")

    def process_request(self, request, **kwargs):
        if not self._proxies:
            return None
        proxy = self._proxies[self._index % len(self._proxies)]
        self._index += 1
        request.meta["proxy"] = proxy
        return None


class RateLimitMiddleware:
    def __init__(self):
        self._domain_timestamps = defaultdict(list)

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        return middleware

    def process_request(self, request, **kwargs):
        domain = urlparse(request.url).netloc
        now = time.time()
        window = self._domain_timestamps[domain]
        window[:] = [t for t in window if now - t < 60]
        request.meta["scrapycoco_domain_hits"] = len(window)
        window.append(now)
        return None


class CookieSessionMiddleware:
    def process_request(self, request, **kwargs):
        if "cookie" not in request.headers:
            request.headers["Cookie"] = ""
        return None


class SmartRetryMiddleware(RetryMiddleware):
    def process_response(self, request, response, spider):
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            spider.logger.warning(f"Retrying {request.url} due to {reason}")
            return self._retry(request, reason, spider) or response
        return response

    def process_exception(self, request, exception, spider):
        spider.logger.warning(f"Retrying {request.url} due to {type(exception).__name__}: {exception}")
        return self._retry(request, exception, spider)
