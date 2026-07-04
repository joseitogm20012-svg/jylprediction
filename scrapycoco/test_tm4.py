"""Find correct Transfermarkt URLs for national teams"""
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

async def try_url(browser, url):
    ctx = await browser.new_context(user_agent=UA, viewport={"width": 1366, "height": 768})
    page = await ctx.new_page()
    result = None
    try:
        await page.goto(url, timeout=15000, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        title = await page.title()
        if "error" not in title.lower() and "404" not in page.url:
            result = {"title": title, "url": page.url}
    except:
        pass
    await ctx.close()
    return result

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        tests = {
            "argentina_en": "https://www.transfermarkt.com/argentina/startseite/verein/35593",
            "argentina_de": "https://www.transfermarkt.com/argentinien/startseite/verein/35593",
            "brazil_en": "https://www.transfermarkt.com/brazil/startseite/verein/35595",
            "brasilien_de": "https://www.transfermarkt.com/brasilien/startseite/verein/35595",
            "germany_en": "https://www.transfermarkt.com/germany/startseite/verein/3220",
            "deutschland_de": "https://www.transfermarkt.com/deutschland/startseite/verein/3220",
            "france_en": "https://www.transfermarkt.com/france/startseite/verein/3377",
            "frankreich_de": "https://www.transfermarkt.com/frankreich/startseite/verein/3377",
            "england_en": "https://www.transfermarkt.com/england/startseite/verein/3399",
            "spain_en": "https://www.transfermarkt.com/spain/startseite/verein/3376",
            "netherlands": "https://www.transfermarkt.com/netherlands/startseite/verein/3379",
        }

        for name, url in tests.items():
            r = await try_url(browser, url)
            if r:
                print("OK %s: %s -> %s" % (name, r["title"][:50], r["url"]))
            else:
                print("FAIL %s: %s" % (name, url))

        await browser.close()

asyncio.run(main())
