"""
Find the correct flashscore URL for World Cup 2026
"""
import asyncio, re
from playwright.async_api import async_playwright

async def cookie_banner(page):
    try:
        btn = await page.query_selector("#onetrust-accept-btn-handler")
        if btn: await btn.click()
    except Exception: pass

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(viewport={"width": 1366, "height": 768})
        page = await ctx.new_page()

        # Start at flashscore homepage to navigate naturally
        await page.goto("https://www.flashscore.es/", timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        await cookie_banner(page)
        await asyncio.sleep(2)
        
        # Get the current URL
        current = page.url
        print(f"Homepage URL: {current}")
        
        # Try to find a link to World Cup
        links = await page.evaluate('''() => {
            const allLinks = document.querySelectorAll('a[href*="mundial"], a[href*="world"], a[href*="World"], a[href*="fifa"], a[href*="FIFA"], a[href*="copa"]');
            return Array.from(allLinks).slice(0, 30).map(a => ({
                href: a.href || a.getAttribute('href'),
                text: a.textContent.trim().slice(0, 60)
            }));
        }''')
        
        print(f"\nLinks relacionados con Mundial/World/FIFA:")
        for l in links:
            print(f"  {l['text']:50s} -> {l['href']}")
        
        # Also check: what tournaments are listed in the sidebar?
        tourneys = await page.evaluate('''() => {
            const items = document.querySelectorAll('a[class*="tournament"], a[class*="event"], [class*="tournament"] a');
            return Array.from(items).slice(0, 20).map(a => ({
                href: a.href || a.getAttribute('href'),
                text: a.textContent.trim().slice(0, 60)
            }));
        }''')
        
        print(f"\nElementos de torneos:")
        for t in tourneys:
            print(f"  {t['text']:50s} -> {t['href']}")
        
        await browser.close()

asyncio.run(main())
