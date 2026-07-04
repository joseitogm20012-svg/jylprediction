"""
SCRAPEO v5 — TM METADATA (no injuries for NT)
Squad page: market_value, average_age, squad_size
Staff page: manager/coach
"""
import json, re, sys, time, asyncio
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from rate_limiter import RateLimiter

_limiter = RateLimiter({"transfermarkt.com": 2.5})

TM_IDS_PATH = Path(__file__).parent / "wc2026_tm_ids.json"
OUT_DIR = Path("C:/Users/Equipo/Desktop/predecirv2/data")
OUT_DIR.mkdir(parents=True, exist_ok=True)
TM_STATS_PATH = OUT_DIR / "transfermarkt_stats.json"
INJURIES_PATH = OUT_DIR / "injuries.json"

log_lines = []

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print("[%s] %s" % (ts, msg))
    log_lines.append("[%s] %s" % (ts, msg))

def display_name(slug):
    overrides = {
        "usa": "USA",
        "south-korea": "South Korea",
        "new-zealand": "New Zealand",
        "costa-rica": "Costa Rica",
        "saudi-arabia": "Saudi Arabia",
        "south-africa": "South Africa",
        "czech-republic": "Czech Republic",
        "turkey": "Türkiye",
    }
    return overrides.get(slug, slug.replace("-", " ").title())

async def consent(page):
    try:
        cf = await page.wait_for_selector("iframe[src*='privacy-mgmt']", timeout=8000)
        if cf:
            frame = await cf.content_frame()
            if frame:
                btn = await frame.wait_for_selector("button:has-text('Accept')", timeout=5000)
                if btn:
                    await btn.click()
                    await asyncio.sleep(2.5)
                    return True
    except:
        pass
    return False

async def scrape_squad_page(page, slug, tm_id):
    """Get market_value, average_age, squad_size"""
    result = {"market_value": "", "average_age": "", "squad_size": ""}
    url = "https://www.transfermarkt.com/%s/startseite/verein/%d" % (slug, tm_id)
    await _limiter.wait("transfermarkt.com")
    await page.goto(url, timeout=30000, wait_until="domcontentloaded")
    await consent(page)
    await asyncio.sleep(3)

    body = await page.inner_text("body")
    html = await page.content()
    soup = BeautifulSoup(html, "html.parser")

    # Market value from body text
    m = re.search(r'([\u20ac€$£][\d.,]+\s*[mbkMBK]?\s*)', body)
    if m:
        result["market_value"] = m.group(1).strip()

    # Squad size & average age from info box
    header = soup.find("div", class_="data-header__info-box")
    if header:
        for li in header.find_all("li", class_="data-header__label"):
            text = li.get_text(" ", strip=True)
            ce = li.find("span", class_="data-header__content")
            if not ce: continue
            val = ce.get_text(strip=True)
            if "Squad size" in text:
                result["squad_size"] = val
            elif "Average age" in text:
                result["average_age"] = val

    return result

async def scrape_staff_page(page, slug, tm_id):
    """Get manager/head coach name"""
    url = "https://www.transfermarkt.com/%s/mitarbeiter/verein/%d" % (slug, tm_id)
    try:
        await _limiter.wait("transfermarkt.com")
        await page.goto(url, timeout=25000, wait_until="domcontentloaded")
        await consent(page)
        await asyncio.sleep(2)

        body = await page.inner_text("body")
        lines = body.split("\n")

        # On TM staff page, the body text layout is:
    #   Lionel Scaloni
    #   Manager
    #   48 ...
    # So we look for a line "Manager" and return the previous non-empty line
        for i, line in enumerate(lines):
            if line.strip() == "Manager":
                # Walk backwards to find the person's name
                for j in range(i - 1, -1, -1):
                    prev = lines[j].strip()
                    if prev and not prev.startswith("Name/Position") and not prev.startswith("COACHING"):
                        return prev
                break
    except:
        pass
    return ""

async def scrape_team(context, slug, tm_id):
    team_display = display_name(slug)
    log(">>> %s (ID %d)" % (team_display, tm_id))

    page = await context.new_page()
    result = {
        "team": team_display,
        "slug": slug,
        "tm_id": tm_id,
        "market_value": "",
        "average_age": "",
        "squad_size": "",
        "manager": "",
        "error": None,
    }

    try:
        squad = await scrape_squad_page(page, slug, tm_id)
        result.update(squad)
        log("  Valor: %s | Edad: %s | Plantilla: %s" % (
            squad["market_value"] or "?",
            squad["average_age"] or "?",
            squad["squad_size"] or "?",
        ))
    except Exception as e:
        log("  ERROR squad: %s" % e)
        result["error"] = str(e)

    try:
        mgr = await scrape_staff_page(page, slug, tm_id)
        result["manager"] = mgr
        log("  DT: %s" % (mgr or "?"))
    except Exception as e:
        log("  ERROR staff: %s" % e)

    await page.close()
    return result

async def main():
    log("=" * 60)
    log("SCRAPEO v5 — TM METADATA")
    log("=" * 60)

    if not TM_IDS_PATH.exists():
        log("ERROR: No se encuentra %s" % TM_IDS_PATH)
        return

    tm_ids = json.loads(TM_IDS_PATH.read_text(encoding="utf-8"))
    log("%d equipos cargados" % len(tm_ids))

    tm_stats_all = {}
    if TM_STATS_PATH.exists():
        try:
            tm_stats_all = json.loads(TM_STATS_PATH.read_text(encoding="utf-8"))
            log("Cargados %d equipos existentes" % len(tm_stats_all))
        except:
            pass

    injuries_all = {}
    if INJURIES_PATH.exists():
        try:
            injuries_all = json.loads(INJURIES_PATH.read_text(encoding="utf-8"))
        except:
            pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1366, "height": 768},
        )

        slugs = list(tm_ids.keys())
        for i, slug in enumerate(slugs, 1):
            # Skip if already done
            if slug in tm_stats_all and tm_stats_all[slug].get("market_value"):
                log("[%d/%d] %s: ya existe, skip" % (i, len(slugs), slug))
                # Still save injuries if any
                if INJURIES_PATH.exists():
                    try:
                        injuries_all = json.loads(INJURIES_PATH.read_text(encoding="utf-8"))
                    except:
                        pass
                continue

            tm_id = tm_ids[slug]
            log("[%d/%d]" % (i, len(slugs)))

            t0 = time.time()
            data = await scrape_team(context, slug, tm_id)
            elapsed = time.time() - t0

            tm_stats_all[slug] = {
                "team": data["team"],
                "slug": slug,
                "tm_id": tm_id,
                "market_value": data["market_value"],
                "average_age": data["average_age"],
                "squad_size": data["squad_size"],
                "manager": data["manager"],
            }

            log("  Hecho en %.1fs" % elapsed)

            TM_STATS_PATH.write_text(json.dumps(tm_stats_all, ensure_ascii=False, indent=2), encoding="utf-8")

            await asyncio.sleep(2)

        await browser.close()

    log("=" * 60)
    complete = sum(1 for v in tm_stats_all.values() if v.get("market_value"))
    log("COMPLETADO: %d/%d equipos con datos" % (complete, len(slugs)))
    log("Output: %s" % TM_STATS_PATH)
    log("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
