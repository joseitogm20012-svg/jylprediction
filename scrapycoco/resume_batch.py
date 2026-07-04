"""
Resume batch: build progress from existing files and continue
"""
import json, asyncio, time
from pathlib import Path
from playwright.async_api import async_playwright
from scrape_all import scrape_one_match, save_match, log

OUT_DIR = Path("C:/Users/Equipo/Desktop/mundial104")
IDS_FILE = OUT_DIR / "all_match_ids.json"
PROGRESS_FILE = OUT_DIR / "progress.json"
MAX_WORKERS = 4

async def worker(wid, browser, mids, done_set):
    for mid in mids:
        if mid in done_set:
            continue
        log("[W%d] %s: comenzando..." % (wid, mid))
        result = await scrape_one_match(mid, browser)
        if result and result.get("error") != "No es Mundial":
            save_match(result)
        log("[W%d] OK %s" % (wid, mid))

async def main():
    with open(IDS_FILE) as f:
        all_ids = json.load(f)

    done = set()
    for fp in OUT_DIR.glob("[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9].json"):
        done.add(fp.stem)
    log("Ya procesados: %d" % len(done))

    remaining = [mid for mid in all_ids if mid not in done]
    log("Restantes: %d" % len(remaining))
    if not remaining:
        log("Todo completado!")
        return

    t0 = time.time()
    async with async_playwright() as p:
        browsers = []
        for i in range(MAX_WORKERS):
            browsers.append(await p.chromium.launch(headless=True))

        chunks = [[] for _ in range(MAX_WORKERS)]
        for i, mid in enumerate(remaining):
            chunks[i % MAX_WORKERS].append(mid)

        tasks = [worker(i, browsers[i], chunks[i], done) for i in range(MAX_WORKERS)]
        await asyncio.gather(*tasks)

        for b in browsers:
            await b.close()

    elapsed = time.time() - t0
    log("=" * 60)
    log("COMPLETADO en %.1f min" % (elapsed / 60))

    # Final count
    final = set()
    for fp in OUT_DIR.glob("[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9].json"):
        final.add(fp.stem)
    log("Total final: %d / %d" % (len(final), len(all_ids)))

if __name__ == "__main__":
    asyncio.run(main())
