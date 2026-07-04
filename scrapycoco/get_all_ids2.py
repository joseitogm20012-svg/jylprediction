"""
Get all WC2026 match IDs from the tournament page
"""
import asyncio, json, re
from playwright.async_api import async_playwright

async def cookie_banner(page):
    try:
        btn = await page.query_selector("#onetrust-accept-btn-handler")
        if btn: await btn.click()
    except Exception: pass

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1366, "height": 768})
        page = await ctx.new_page()

        # Try to access the World Cup tournament page
        urls_to_try = [
            "https://www.flashscore.com.ve/futbol/mundial/campeonato-del-mundo/resultados/",
            "https://www.flashscore.com.ve/futbol/mundial/campeonato-del-mundo/",
            "https://www.flashscore.com.ve/futbol/mundial/campeonato-del-mundo/calendario/",
        ]
        
        all_ids = set()
        
        for url in urls_to_try:
            print(f"\nProbando: {url}")
            try:
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await asyncio.sleep(5)
                await cookie_banner(page)
                await asyncio.sleep(3)
                
                # Save page
                html = await page.content()
                safe_name = url.rstrip('/').split('/')[-1] or 'index'
                with open(f"C:/Users/Equipo/Desktop/mundial104/debug_{safe_name}.html", "w", encoding="utf-8") as f:
                    f.write(html)
                
                print(f"  Title: {await page.title()}")
                
                # Extract all links with /partido/ that have match IDs
                ids_from_page = await page.evaluate('''() => {
                    const links = document.querySelectorAll('a[href*="/partido/"]');
                    const ids = new Set();
                    for (const a of links) {
                        const m = a.href.match(/[?&]mid=([a-zA-Z0-9]{8})/);
                        if (m) ids.add(m[1]);
                        const m2 = a.href.match(/\/partido\/[^/]+\/([a-zA-Z0-9]{8})\//);
                        if (m2) ids.add(m2[1]);
                        const m3 = a.href.match(/\/partido\/([a-zA-Z0-9]{8})\//);
                        if (m3) ids.add(m3[1]);
                    }
                    return Array.from(ids);
                }''')
                
                print(f"  IDs encontrados: {len(ids_from_page)}")
                if ids_from_page:
                    print(f"  Ejemplos: {ids_from_page[:5]}")
                    all_ids.update(ids_from_page)
                
                # Also check for event__match divs which are match containers
                match_events = await page.evaluate('''() => {
                    const matches = document.querySelectorAll('[class*="event__match"]');
                    const ids = new Set();
                    for (const m of matches) {
                        const links = m.querySelectorAll('a');
                        for (const a of links) {
                            const href = a.href || a.getAttribute('href') || '';
                            const match = href.match(/[?&]mid=([a-zA-Z0-9]{8})/);
                            if (match) ids.add(match[1]);
                        }
                    }
                    return Array.from(ids);
                }''')
                print(f"  IDs desde event__match: {len(match_events)}")
                if match_events:
                    all_ids.update(match_events)
                
            except Exception as e:
                print(f"  Error: {e}")

        # Also scrape from the homepage - it shows live WC matches
        print(f"\nProbando homepage para partidos del Mundial...")
        await page.goto("https://www.flashscore.com.ve/", timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(5)
        await cookie_banner(page)
        await asyncio.sleep(3)
        
        # Look for World Cup matches on the homepage
        wc_ids = await page.evaluate('''() => {
            const allLinks = document.querySelectorAll('a');
            const ids = new Set();
            for (const a of allLinks) {
                const text = (a.textContent || '').toLowerCase();
                const href = a.href || '';
                if ((text.includes('mundial') || text.includes('world cup')) && href.includes('mid=')) {
                    const m = href.match(/[?&]mid=([a-zA-Z0-9]{8})/);
                    if (m) ids.add(m[1]);
                }
            }
            return Array.from(ids);
        }''')
        print(f"  WC IDs desde homepage: {len(wc_ids)}")
        if wc_ids:
            all_ids.update(wc_ids)

        print(f"\n\nTOTAL IDs UNICOS: {len(all_ids)}")
        ids_list = sorted(all_ids)
        print(f"IDs: {ids_list}")
        
        with open("C:/Users/Equipo/Desktop/mundial104/all_match_ids.json", "w") as f:
            json.dump(ids_list, f, indent=2)
        print("\nGuardados en all_match_ids.json")
        
        await browser.close()

asyncio.run(main())
