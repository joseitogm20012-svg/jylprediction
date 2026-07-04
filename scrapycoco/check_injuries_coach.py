"""Check TM injuries page + coach location"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1366, "height": 768},
        )
        page = await context.new_page()

        async def consent():
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

        # Check Argentina injuries page
        print("=== ARGENTINA INJURIES ===")
        await page.goto("https://www.transfermarkt.com/argentina/verletzungen/verein/3437", timeout=30000)
        await asyncio.sleep(2)
        await consent()
        await asyncio.sleep(3)

        body = await page.inner_text("body")
        # Check for injury-related keywords
        for kw in ["Injury", "Verletzung", "Muscle", "Knee", "Ankle", "Hamstring", "Calf", "Groin"]:
            if kw.lower() in body.lower():
                print("FOUND keyword: %s" % kw)
        print("Body text (first 1000 chars):")
        print(body[:1000])

        # Check if there's a "No injuries" message
        if "no injuries" in body.lower() or "no data" in body.lower():
            print("No injuries message found")

        # Check staff page for coach
        print("\n=== ARGENTINA STAFF ===")
        await page.goto("https://www.transfermarkt.com/argentina/mitarbeiter/verein/3437", timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        await consent()
        await asyncio.sleep(3)

        body2 = await page.inner_text("body")
        # Look for manager/coach
        for kw in ["Manager", "Coach", "Trainer", "Head coach", "Entrenador"]:
            if kw in body2:
                idx = body2.index(kw)
                print("FOUND '%s' at idx %d: %s" % (kw, idx, body2[max(0,idx-50):idx+100]))
        print("Body first 1500:")
        print(body2[:1500])

        await browser.close()

asyncio.run(main())
