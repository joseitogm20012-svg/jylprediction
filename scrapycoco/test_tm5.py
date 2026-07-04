"""Find correct national team IDs via Transfermarkt autocomplete"""
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(user_agent=UA, viewport={"width": 1366, "height": 768})
        page = await ctx.new_page()

        # Try to find Argentina national team on TM
        # Method 1: Go to nations page
        await page.goto("https://www.transfermarkt.com/wettbewerbe/national/wettbewerbe", timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        html = await page.content()
        Path("debug_nations.html").write_text(html, encoding="utf-8")

        soup = BeautifulSoup(html, "html.parser")
        print("=== Looking for national team links ===")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            if "nationalmannschaft" in href or any(nat in href for nat in ["/argentinien", "/brasilien", "/frankreich"]):
                full_url = "https://www.transfermarkt.com" + href
                print("  NAT: %s -> %s" % (text[:40], full_url))

        await ctx.close()
        await browser.close()

asyncio.run(main())
