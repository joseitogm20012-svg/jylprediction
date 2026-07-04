"""
Re-fetch missing scores for 10 past matches that have no result
"""
import json, asyncio, re
from pathlib import Path
from playwright.async_api import async_playwright

OUT_DIR = Path("C:/Users/Equipo/Desktop/mundial104")
MISSING = ["f7ENGzPc", "hEWfCwid", "Iiqjm5Pq", "jaMlPbx1", "jRyHEZGP",
           "KMRMTaNM", "n7TsyKKD", "n9TEVLhA", "nRFcNx7D", "Olnboqfd"]

async def cookie_banner(page):
    try:
        btn = await page.query_selector("#onetrust-accept-btn-handler")
        if btn: await btn.click()
    except Exception: pass

async def fix_match(mid, browser):
    page = await browser.new_page()
    try:
        url = "https://www.flashscore.es/partido/%s/" % mid
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(4)
        await cookie_banner(page)
        await asyncio.sleep(2)

        # Try multiple selectors for score
        score = ""
        for sel in [
            "div[class*='detailScore__wrapper']",
            "div[class*='score']",
            "*[class*='detailScore']",
            "*[data-testid*='score']",
            "*[class*='matchScore']",
        ]:
            try:
                el = await page.query_selector(sel)
                if el:
                    t = (await el.text_content()).strip()
                    if t and t != "-":
                        score = t
                        break
            except: pass

        # Also try from the match header/title
        if not score:
            try:
                title = await page.title()
                m = re.search(r'(\d+)\s*[-–:]\s*(\d+)', title)
                if m:
                    score = m.group(1) + "-" + m.group(2)
            except: pass

        # Update JSON
        fp = OUT_DIR / ("%s.json" % mid)
        if fp.exists():
            with open(fp, encoding="utf-8") as f:
                data = json.load(f)
            if score:
                data["score"] = score
                print("  %s: score encontrado -> %s" % (mid, score))
            else:
                # Still no score, try broader selector
                try:
                    body_text = await page.evaluate('() => document.body.innerText')
                    m = re.search(r'(\d+)\s*[-–]\s*(\d+)\s*Finalizado|Finalizado\s*(\d+)\s*[-–]\s*(\d+)', body_text)
                    if m:
                        g = m.groups()
                        score = (g[0] or g[2]) + "-" + (g[1] or g[3])
                        data["score"] = score
                        print("  %s: score desde body -> %s" % (mid, score))
                    else:
                        print("  %s: NO se encontro score" % mid)
                except: pass
            with open(fp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            print("  %s: archivo no existe" % mid)
    except Exception as e:
        print("  %s: ERROR %s" % (mid, e))
    finally:
        await page.close()

async def main():
    print("Rescrapeando %d partidos sin score..." % len(MISSING))
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for mid in MISSING:
            print("Procesando %s..." % mid)
            await fix_match(mid, browser)
        await browser.close()

    # Final count
    with_score = 0
    for fp in sorted(OUT_DIR.glob("[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9].json")):
        with open(fp, encoding="utf-8") as f:
            data = json.load(f)
        s = (data.get("score") or "").strip()
        if s and s != "-":
            with_score += 1
    print("\nTotal con resultado: %d / 93" % with_score)

asyncio.run(main())
