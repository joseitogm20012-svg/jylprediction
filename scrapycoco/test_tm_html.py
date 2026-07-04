"""Test: examine TM HTML after consent acceptance"""
import asyncio, json
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
        )
        page = await context.new_page()
        await page.goto("https://www.transfermarkt.com/argentina/startseite/verein/3437", timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        # Try clicking iframe consent
        iframes = page.frames
        print("Frames:", len(iframes))
        for i, f in enumerate(iframes):
            if "sourcepoint" in f.url or "consent" in f.url:
                print("  Frame %d: %s" % (i, f.url[:100]))
                for sel in ["button[title='Accept']", "button:has-text('Accept')", "button:has-text('AGREE')"]:
                    btn = await f.query_selector(sel)
                    if btn:
                        print("  Clicking: %s" % sel)
                        await btn.click()
                        await asyncio.sleep(2)

        await asyncio.sleep(3)
        html = await page.content()

        # Save raw HTML
        open("test_argentina.html", "w", encoding="utf-8").write(html)
        print("Saved test_argentina.html (%d chars)" % len(html))

        # Check for key content
        checks = ["data-header", "Total market value", "Gesamtmarktwert", "Average age", "Squad size", "Manager", "Coach"]
        for c in checks:
            if c in html:
                print("FOUND: %s" % c)

        # Body text
        body = await page.query_selector("body")
        if body:
            txt = await body.inner_text()
            print("Body text (first 2000 chars):")
            print(txt[:2000])

        await browser.close()

asyncio.run(test())
