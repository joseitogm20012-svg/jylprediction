"""Capture ALL network requests from FlashScore match page."""
import asyncio, json
from playwright.async_api import async_playwright

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = await context.new_page()
        
        all_responses = []
        async def handle_response(response):
            url = response.url
            status = response.status
            if len(url) > 20:
                all_responses.append(f"{status} {url[:120]}")
        page.on("response", handle_response)
        
        # Navigate  
        url = "https://www.flashscore.com/match/4UXzDy1d/#/match-summary/match-statistics"
        print(f"Loading match page...")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
        except Exception as e:
            print(f"Goto error: {e}")
        
        print(f"Waiting 15s for data...")
        await asyncio.sleep(15)
        
        print(f"\n=== ALL RESPONSES ({len(all_responses)}) ===")
        for r in all_responses[-30:]:  # Show last 30
            print(f"  {r}")
        
        # Try clicking/activating the statistics tab if needed  
        print(f"\nChecking page title: {await page.title()}")
        
        await browser.close()

asyncio.run(check())