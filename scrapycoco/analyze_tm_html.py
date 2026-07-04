"""Analyze TM squad page HTML structure"""
import asyncio, json
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1366, "height": 768},
        )
        page = await context.new_page()

        # Handle consent
        async def handle_consent():
            try:
                cf = await page.wait_for_selector("iframe[src*='privacy-mgmt']", timeout=8000)
                if cf:
                    frame = await cf.content_frame()
                    if frame:
                        btn = await frame.wait_for_selector("button:has-text('Accept')", timeout=5000)
                        if btn:
                            await btn.click()
                            await asyncio.sleep(3)
            except:
                pass

        await page.goto("https://www.transfermarkt.com/argentina/startseite/verein/3437", timeout=30000)
        await asyncio.sleep(2)
        await handle_consent()
        await asyncio.sleep(3)

        html = await page.content()
        s = BeautifulSoup(html, "html.parser")

        # Analyze data-header
        header = s.find(class_="data-header")
        if header:
            print("=== data-header full HTML ===")
            print(header.prettify()[:3000])
            print()

            # Look for data-header__info-box or data-header__info
            info = header.find(class_="data-header__info-box")
            if info:
                print("=== data-header__info-box ===")
                print(info.prettify()[:2000])
            else:
                # Try other info containers
                for c in ["data-header__info", "data-header__details", "data-header__content"]:
                    el = header.find(class_=c)
                    if el:
                        print("Found class: %s" % c)
                        print(el.prettify()[:500])

            # All span labels
            print("\n=== All spans with data-header__label ===")
            for sp in header.find_all("span", class_="data-header__label"):
                print("Span: %s" % repr(sp.get_text(strip=True)))
                parent = sp.find_parent()
                print("  Parent class: %s" % parent.get("class", ""))
                print("  Parent HTML: %s" % parent.prettify()[:300])
            print()

        # Also look for box with info about the team
        for cls in ["info-box", "info", "header-info", "verein-data", "team-info"]:
            el = s.find(class_=cls)
            if el:
                print("Found class: %s" % cls)
                print(el.get_text(strip=True)[:500])
                print()

        # Check what surrounds "Total market value"
        if "Total market value" in html:
            idx = html.index("Total market value")
            before = html[max(0,idx-500):idx]
            after = html[idx:idx+500]
            print("=== Context before 'Total market value' ===")
            print(before[:300])
            print("=== Context after 'Total market value' ===")
            print(after[:300])

        await browser.close()

asyncio.run(main())
