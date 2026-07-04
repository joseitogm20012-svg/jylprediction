"""Finish last 2 matches"""
import asyncio
from playwright.async_api import async_playwright
from scrape_all import scrape_one_match, save_match, log

async def main():
    mids = ["zP64Ye2M", "zmvgtcCa"]
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for mid in mids:
            log("Procesando: %s" % mid)
            result = await scrape_one_match(mid, browser)
            if result and result.get("error") != "No es Mundial":
                save_match(result)
                log("OK %s: %s" % (mid, result.get("score", "?")))
            else:
                log("Skip %s" % mid)
        await browser.close()
    log("FIN!")

asyncio.run(main())
