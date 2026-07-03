"""Per-domain async rate limiter for Playwright scrapers."""
import asyncio
import time
from typing import Optional


class RateLimiter:
    def __init__(self, defaults: dict = None):
        self._last_hit: dict[str, float] = {}
        self._delays: dict[str, float] = defaults or {}

    def set_delay(self, domain: str, seconds: float):
        self._delays[domain] = seconds

    async def wait(self, domain: str):
        now = time.time()
        last = self._last_hit.get(domain, 0.0)
        elapsed = now - last
        needed = self._delays.get(domain, 1.0)
        if elapsed < needed:
            await asyncio.sleep(needed - elapsed)
        self._last_hit[domain] = time.time()

    def wait_sync(self, domain: str):
        """Synchronous version for non-async contexts."""
        now = time.time()
        last = self._last_hit.get(domain, 0.0)
        elapsed = now - last
        needed = self._delays.get(domain, 1.0)
        if elapsed < needed:
            time.sleep(needed - elapsed)
        self._last_hit[domain] = time.time()
