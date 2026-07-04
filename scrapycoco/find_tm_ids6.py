"""
Extract all 48 TM team IDs from the WC2026 page group tables
"""
import asyncio, json, re
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

        # Navigate to WC page
        print("Navigating to WC page...")
        await page.goto("https://www.transfermarkt.com/weltmeisterschaft/startseite/pokalwettbewerb/FIWC", timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(4)

        # Handle consent
        try:
            for f in page.frames:
                if "consent" in f.url or "privacy" in f.url:
                    btn = f.locator("button:has-text('Accept')")
                    if await btn.count() > 0:
                        await btn.click()
                        print("Consent accepted")
                        await asyncio.sleep(3)
                        break
        except Exception as e:
            print("Consent error:", e)

        # Wait and scroll
        await page.evaluate("window.scrollTo(0, 500)")
        await asyncio.sleep(2)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)

        html = await page.content()
        Path("debug_wc_final.html").write_text(html, encoding="utf-8")
        print("Page saved: %d bytes" % len(html))

        # Find all team links
        soup = BeautifulSoup(html, "html.parser")
        
        # Method 1: find all anchor tags with /verein/ in URL
        teams = {}
        for a in soup.find_all("a", href=True):
            href = a["href"]
            m = re.search(r'/verein/(\d+)', href)
            if m:
                tid = int(m.group(1))
                # Get the team name - look for img alt or text
                img = a.find("img")
                if img and img.get("alt"):
                    name = img["alt"].strip()
                    if name and name not in teams:
                        teams[name] = tid
                        print("  %s: %d" % (name, tid))

        print("\n=== ALL TEAMS FOUND (%d) ===" % len(teams))
        for name in sorted(teams.keys()):
            print("  %s: %d" % (name, teams[name]))

        Path("tm_wc_ids.json").write_text(json.dumps(teams, ensure_ascii=False, indent=2), encoding="utf-8")

        await ctx.close()
        await browser.close()

asyncio.run(main())
