"""Finish remaining matches"""
import json, asyncio
from pathlib import Path
from playwright.async_api import async_playwright
from scrape_all import scrape_one_match, save_match, log

OUT_DIR = Path("C:/Users/Equipo/Desktop/mundial104")
IDS_FILE = OUT_DIR / "all_match_ids.json"

async def main():
    with open(IDS_FILE) as f:
        all_ids = json.load(f)
    
    done = set()
    for fp in OUT_DIR.glob("[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9].json"):
        done.add(fp.stem)
    
    remaining = [mid for mid in all_ids if mid not in done]
    log("Restantes: %d" % len(remaining))
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for mid in remaining:
            log("Procesando: %s" % mid)
            result = await scrape_one_match(mid, browser)
            if result and result.get("error") != "No es Mundial":
                save_match(result)
                log("OK %s: %s" % (mid, result.get("score", "?")))
            else:
                log("Skip %s" % mid)
        await browser.close()
    
    final = set()
    for fp in OUT_DIR.glob("[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9].json"):
        final.add(fp.stem)
    log("Total final: %d / %d" % (len(final), len(all_ids)))

asyncio.run(main())
