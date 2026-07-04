"""Map all national team IDs from Transfermarkt"""
import asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright
import re

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        mapping = {}
        
        # Check range 3436 to 3700
        for tid in range(3436, 3700):
            ctx = await browser.new_context(user_agent=UA, viewport={"width": 1366, "height": 768})
            page = await ctx.new_page()
            try:
                await page.goto("https://www.transfermarkt.com/argentina/startseite/verein/%d" % tid, timeout=10000, wait_until="domcontentloaded")
                await asyncio.sleep(1)
                title = await page.title()
                if "error" not in title.lower() and "404" not in title:
                    html = await page.content()
                    # Extract team name from h1
                    m = re.search(r'<span class="data-header__flag">.*?<img[^>]*alt="([^"]*)"', html, re.DOTALL)
                    name = m.group(1) if m else title.split(" - ")[0]
                    mapping[name] = tid
                    print("ID %d: %s" % (tid, name))
            except: pass
            finally:
                await ctx.close()
            if tid % 20 == 0:
                print("  ... checked up to %d, found %d teams" % (tid, len(mapping)))
        
        print("\n\n=== ALL NATIONAL TEAMS ===")
        for name in sorted(mapping.keys()):
            print("%s: %d" % (name, mapping[name]))
        
        Path("tm_national_ids.json").write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
        await browser.close()

asyncio.run(main())
