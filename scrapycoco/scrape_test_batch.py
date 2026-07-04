"""Test batch scraping with 3 matches"""
import asyncio, json
from scrape_all import scrape_one_match, save_match, log
from playwright.async_api import async_playwright

TEST_IDS = ["4UXzDy1d", "vPsIXWOb", "O4oeJu9d", "rgxknWwh", "4rOtRK7l"]

async def main():
    log("Test batch con %d matches" % len(TEST_IDS))
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for mid in TEST_IDS:
            log("\n--- %s ---" % mid)
            result = await scrape_one_match(mid, browser)
            if result and not result.get("error"):
                save_match(result)
                log("%s: %d stats, %d/%d titulares" % (
                    mid,
                    len(result.get("estadisticas", {})),
                    len(result.get("alineaciones", {}).get("local", {}).get("titulares", [])),
                    len(result.get("alineaciones", {}).get("visitante", {}).get("titulares", []))
                ))
            else:
                log("%s: %s" % (mid, result.get("error") if result else "None"))
        await browser.close()

asyncio.run(main())
