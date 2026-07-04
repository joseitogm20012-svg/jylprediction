"""Test: search Transfermarkt directly for Argentina"""
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

        # Try Transfermarkt's own search
        search_url = "https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query=Argentina+national+team"
        print("Searching:", search_url)
        await page.goto(search_url, timeout=25000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        html = await page.content()
        Path("debug_tm.html").write_text(html, encoding="utf-8")

        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a", href=True)
        print("Total links:", len(links))

        # Look for squad page links
        for a in links:
            href = a["href"]
            text = a.get_text(strip=True)
            if "startseite" in href and "verein" in href:
                print("SQUAD:", text[:50], "->", href)

        # Try the data-header approach
        header = soup.find(class_="data-header")
        if header:
            print("HEADER FOUND")
            for span in header.find_all("span", class_="data-header__label"):
                print("  Label:", span.get_text(strip=True))
        else:
            print("NO HEADER")

        await ctx.close()
        await browser.close()

asyncio.run(main())
