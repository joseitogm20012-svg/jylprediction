"""Quick test: search Transfermarkt URL for Argentina"""
import asyncio, json
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(user_agent=UA, viewport={"width": 1366, "height": 768})
        page = await ctx.new_page()

        await page.goto("https://www.google.com/search?q=site:transfermarkt.com+Argentina+national+team+squad+startseite", timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(2)

        html = await page.content()
        Path("debug_google.html").write_text(html, encoding="utf-8")

        soup = BeautifulSoup(html, "html.parser")
        links = [(a.get_text(strip=True)[:60], a["href"][:200]) for a in soup.find_all("a", href=True) if "transfermarkt" in a["href"]]
        print("Links encontrados:", len(links))
        for text, href in links[:5]:
            print("  [%s]" % href.split("&")[0])
            print("  -> %s" % text)

        el = await page.query_selector('a[href*="transfermarkt.com/"]')
        if el:
            href = await el.get_attribute("href")
            print("PRIMER LINK:", href.split("&")[0] if href else "NONE")
        else:
            print("NO LINK CON query_selector")

        await ctx.close()
        await browser.close()

asyncio.run(main())
