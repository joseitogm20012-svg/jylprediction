"""Handle consent and find Argentina's national team page"""
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

async def accept_consent(page):
    try:
        # Wait for iframe
        frame = page.frame_locator("iframe[title*='SP Consent']")
        btn = frame.first.locator("button:has-text('Accept')")
        await btn.click(timeout=5000)
        await asyncio.sleep(2)
        print("  Consent accepted")
        return
    except: pass
    try:
        # Try different selectors
        for sel in ["button:has-text('Accept All')", "button:has-text('Continue')", "#accept-cookies", ".sp_choice_type_11"]:
            try:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    await asyncio.sleep(2)
                    print("  Consent clicked:", sel)
                    return
            except: pass
    except: pass
    print("  No consent button found")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(user_agent=UA, viewport={"width": 1366, "height": 768})
        page = await ctx.new_page()

        page.on("dialog", lambda d: d.accept())

        print("Navigating to nations page...")
        await page.goto("https://www.transfermarkt.com/wettbewerbe/national/wettbewerbe", timeout=25000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        await accept_consent(page)

        # Wait for content to load after consent
        await asyncio.sleep(3)

        html = await page.content()
        Path("debug_nations2.html").write_text(html, encoding="utf-8")
        print("Page saved: %d bytes" % len(html))

        soup = BeautifulSoup(html, "html.parser")
        # Look for any links containing national team names
        keywords = ["argentina", "argentinien", "nationalmannschaft", "national team", "startseite"]
        found = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)
            for kw in keywords:
                if kw in href.lower() or (kw in text.lower()):
                    found.append((text[:50], href[:120]))
                    break
        print("Found %d relevant links" % len(found))
        for text, href in found[:15]:
            print("  %s -> %s" % (text, href))

        await ctx.close()
        await browser.close()

asyncio.run(main())
