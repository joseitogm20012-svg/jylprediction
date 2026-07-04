"""Discover Transfermarkt team IDs for all 48 WC teams"""
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

# Known correct IDs
KNOWN = {
    "argentina": 3437,
    "brazil": 3439,
}

# English slugs to try
TEAMS = [
    "argentina", "brazil", "australia", "cameroon",
    "spain", "nigeria", "usa", "saudi-arabia",
    "poland", "south-korea", "egypt",
    "france", "denmark", "tunisia", "canada",
    "england", "serbia", "iran", "jamaica",
    "portugal", "morocco", "paraguay", "new-zealand",
    "belgium", "croatia", "ecuador", "costa-rica",
    "netherlands", "senegal", "qatar", "panama",
    "italy", "colombia", "japan", "algeria",
    "mexico", "switzerland", "greece", "bolivia",
    "uruguay", "south-africa", "chile", "honduras",
    "czech-republic", "turkey", "guatemala", "indonesia",
    "germany",
]

async def check_id(browser, slug, tid):
    ctx = await browser.new_context(user_agent=UA, viewport={"width": 1366, "height": 768})
    page = await ctx.new_page()
    url = "https://www.transfermarkt.com/%s/startseite/verein/%s" % (slug, tid)
    try:
        await page.goto(url, timeout=10000, wait_until="domcontentloaded")
        await asyncio.sleep(1.5)
        title = await page.title()
        if "error" not in title.lower():
            return title
    except: pass
    finally:
        await ctx.close()
    return None

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Try a range of IDs for Argentina and Brazil
        # We know: ARG=3437, BRA=3439
        # Try nearby IDs to see if there's a pattern
        for slug in ["argentina", "france", "england", "germany", "spain", "netherlands"]:
            for tid in range(3430, 3460):
                result = await check_id(browser, slug, tid)
                if result:
                    print("%s ID %d: %s" % (slug, tid, result[:60]))
                    break
                await asyncio.sleep(0.2)

        await browser.close()

asyncio.run(main())
