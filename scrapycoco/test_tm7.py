"""
Navigate WC page, click consent iframe, extract participant teams
"""
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

        page.on("dialog", lambda d: d.accept())

        # Go to WC page
        await page.goto("https://www.transfermarkt.com/weltmeisterschaft/startseite/pokalwettbewerb/FIWC", timeout=25000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Try clicking consent in iframe
        try:
            iframes = page.frames
            for f in iframes:
                if "consent" in f.url or "privacy" in f.url or "sp" in f.url:
                    print("Consent iframe:", f.url[:100])
                    accept = f.locator("button:has-text('Accept')")
                    if await accept.count() > 0:
                        await accept.click()
                        print("Clicked accept in iframe")
                        await asyncio.sleep(2)
        except Exception as e:
            print("Iframe consent fail:", e)

        # Click by role if available
        try:
            accept = page.get_by_role("button", name="Accept")
            if await accept.count() > 0:
                await accept.first.click()
                print("Clicked Accept button")
                await asyncio.sleep(3)
        except: pass

        # Force scroll to load content
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)

        html = await page.content()
        Path("debug_wc2.html").write_text(html, encoding="utf-8")

        # Search for team links in the rendered page
        soup = BeautifulSoup(html, "html.parser")
        
        # Teams table - look for table rows with team names
        tables = soup.find_all("table", class_="items")
        print("Tables found:", len(tables))
        for i, table in enumerate(tables):
            rows = table.find_all("tr")
            for row in rows[:30]:
                text = row.get_text(strip=True)[:100]
                if text:
                    # Find anchor with squad link
                    a = row.find("a", href=lambda h: h and "verein" in h and ("kader" in h or "startseite" in h))
                    if a:
                        print("  Row: %s -> %s" % (text[:60], a["href"]))

        # Also search all anchor tags for team names
        print("\n=== All 'verein' links ===")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "verein" in href and ("kader" in href or "startseite" in href):
                txt = a.get_text(strip=True)
                img = a.find("img")
                if img:
                    txt = img.get("alt", "") or txt
                print("  %s -> %s" % (str(txt)[:40], href[:100]))

        await ctx.close()
        await browser.close()

asyncio.run(main())
