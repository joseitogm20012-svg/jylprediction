"""Quick Playwright check of a few known TM IDs"""
import asyncio
from playwright.async_api import async_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

async def check(browser, slug, tid):
    ctx = await browser.new_context(user_agent=UA, viewport={"width": 1366, "height": 768})
    page = await ctx.new_page()
    try:
        # Accept consent
        await page.goto("https://www.transfermarkt.com/%s/startseite/verein/%d" % (slug, tid), timeout=15000, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        title = await page.title()
        if "error" not in title.lower() and "404" not in title:
            html = await page.content()
            name = ""
            import re
            m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
            if m:
                name = m.group(1).strip()[:40]
            print("  %s/%d: %s [%s]" % (slug, tid, name, title[:50]))
            return title
    except Exception as e:
        print("  %s/%d: ERROR %s" % (slug, tid, str(e)[:40]))
    finally:
        await ctx.close()
    return None

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Check Argentina 3437 (known good)
        print("Verifying known IDs:")
        await check(browser, "argentina", 3437)
        await check(browser, "brazil", 3439)
        
        # Check nearby IDs for other teams
        print("\nTrying nearby IDs (3436-3450):")
        for tid in range(3436, 3451):
            if tid in (3437, 3439): continue
            t = await check(browser, "argentina", tid)
            if t:
                # Found something - check if it's a national team
                pass
            await asyncio.sleep(0.5)

        await browser.close()

asyncio.run(main())
