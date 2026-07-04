"""Test: navigate World Cup page for team IDs"""
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(user_agent=UA, viewport={"width": 1366, "height": 768})
        page = await ctx.new_page()

        # World Cup 2026 page
        await page.goto("https://www.transfermarkt.com/weltmeisterschaft/startseite/pokalwettbewerb/FIWC", timeout=25000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        html = await page.content()
        Path("debug_wc.html").write_text(html, encoding="utf-8")

        soup = BeautifulSoup(html, "html.parser")

        # Find all participant/team links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if "startseite" in href and "verein" in href:
                print("TEAM:", text[:40], "->", href)
            elif "kader" in href and "verein" in href:
                print("SQUAD:", text[:40], "->", href)

        await ctx.close()
        await browser.close()

asyncio.run(main())
