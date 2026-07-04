"""Test: examine TM HTML after consent acceptance (v2)"""
import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
        )
        page = await context.new_page()

        # Listen for popup/redirect after consent
        async def handle_consent():
            try:
                # Wait for consent iframe to appear
                consent_frame = await page.wait_for_selector("iframe[src*='privacy-mgmt']", timeout=8000)
                if consent_frame:
                    frame = await consent_frame.content_frame()
                    if frame:
                        # Click Accept
                        btn = await frame.wait_for_selector("button:has-text('Accept')", timeout=5000)
                        if btn:
                            await btn.click()
                            print("Clicked Accept in iframe")
                            await asyncio.sleep(3)
            except Exception as e:
                print("Consent handling: %s" % e)

        await page.goto("https://www.transfermarkt.com/argentina/startseite/verein/3437", timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        await handle_consent()

        # Wait for real content
        await asyncio.sleep(3)
        html = await page.content()
        open("test_argentina2.html", "w", encoding="utf-8").write(html)
        print("Saved test_argentina2.html (%d chars)" % len(html))

        # Check for key content
        checks = ["data-header", "Total market value", "Gesamtmarktwert", "Average age",
                   "Squad size", "Manager", "Coach", "Argentina", "team__name"]
        for c in checks:
            if c in html:
                print("FOUND: %s" % c)
            else:
                print("NOT FOUND: %s" % c)

        # Body or main content
        body = await page.query_selector("body")
        if body:
            txt = await body.inner_text()
            print("\nBody text (first 2000 chars):")
            print(txt[:2000])

        # Check if there is a tm-team or header element
        team_header = await page.query_selector(".data-header, .info-header, .team-header, .verein-header")
        if team_header:
            print("\nTeam header found!")
            print(await team_header.inner_text())
        else:
            print("\nNo team header found")

        await browser.close()

asyncio.run(test())
