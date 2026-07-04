"""
SCRAPEO v4 — Playwright + parsing directo de IDs TM
Acepta consent wall SourcePoint.
Usa li.data-header__label y extrae valor del inner_text.
"""
import json, re, sys, time, asyncio
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

TM_IDS_PATH = Path(__file__).parent / "wc2026_tm_ids.json"
OUT_DIR = Path("C:/Users/Equipo/Desktop/predecirv2/data")
OUT_DIR.mkdir(parents=True, exist_ok=True)
INJURIES_PATH = OUT_DIR / "injuries.json"
TM_STATS_PATH = OUT_DIR / "transfermarkt_stats.json"

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

async def handle_consent(page):
    """Accept SourcePoint consent wall."""
    try:
        cf = await page.wait_for_selector("iframe[src*='privacy-mgmt']", timeout=8000)
        if cf:
            frame = await cf.content_frame()
            if frame:
                btn = await frame.wait_for_selector("button:has-text('Accept')", timeout=5000)
                if btn:
                    await btn.click()
                    log("  Consent aceptado")
                    await asyncio.sleep(2.5)
                    return True
    except:
        pass
    return False

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
        "injuries": [],
        "error": None,
    }

    try:
        # ── SQUAD PAGE ──
        squad_url = "https://www.transfermarkt.com/%s/startseite/verein/%d" % (slug, tm_id)
        log("  URL: %s" % squad_url)
        await page.goto(squad_url, timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        await handle_consent(page)
        await asyncio.sleep(3)

        # Get rendered text (includes JS-injected content)
        body_text = await page.inner_text("body")

        # Parse HTML with BS4
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # Extract from body text for market value
        # Pattern: after "World Cup" or competition name, before "Total market value"
        m = re.search(r'([€$£][\d.,]+\s*[mbkMBK]?\s*)\s*Total market value', body_text)
        if m:
            result["market_value"] = m.group(1).strip()
        else:
            # Try other patterns
            m = re.search(r'(?:Total market value|Gesamtmarktwert)[:\s]*(\S[\d.,]+\s*(?:mio|mill|Mio\.?)?\s*(?:€|m|M))', body_text, re.IGNORECASE)
            if m:
                result["market_value"] = m.group(1).strip()

        # Parse from header labels (li.data-header__label)
        header = soup.find("div", class_="data-header__info-box")
        if header:
            for li in header.find_all("li", class_="data-header__label"):
                text = li.get_text(" ", strip=True)
                content_el = li.find("span", class_="data-header__content")
                if not content_el:
                    continue
                val = content_el.get_text(strip=True)

                if "Squad size" in text:
                    result["squad_size"] = val
                elif "Average age" in text or "Edad media" in text:
                    result["average_age"] = val

        log("  Valor: %s | Edad: %s | Plantilla: %s" % (
            result["market_value"] or "?",
            result["average_age"] or "?",
            result["squad_size"] or "?",
        ))

        # ── INJURIES PAGE ──
        injury_url = "https://www.transfermarkt.com/%s/verletzungen/verein/%d" % (slug, tm_id)
        log("  Lesiones: %s" % injury_url)
        try:
            await page.goto(injury_url, timeout=25000, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            await handle_consent(page)
            await asyncio.sleep(2)

            ih = await page.content()
            isoup = BeautifulSoup(ih, "html.parser")
            itable = isoup.find("table", class_="items")
            if itable:
                for tr in itable.find_all("tr"):
                    tds = tr.find_all("td")
                    if len(tds) >= 3:
                        player = tds[0].get_text(strip=True)
                        injury = tds[1].get_text(strip=True)
                        status = tds[2].get_text(strip=True)
                        if player and injury:
                            result["injuries"].append({
                                "player": player,
                                "injury": injury,
                                "status": status,
                            })
                log("  Lesiones: %d" % len(result["injuries"]))
            else:
                log("  Sin tabla de lesiones")
        except Exception as e:
            log("  Error lesiones: %s" % e)

    except Exception as e:
        log("  ERROR %s: %s" % (slug, e))
        result["error"] = str(e)
    finally:
        await page.close()

    return result

async def main():
    log("=" * 60)
    log("SCRAPEO v4 — PLAYWRIGHT + IDs DIRECTOS")
    log("=" * 60)

    if not TM_IDS_PATH.exists():
        log("ERROR: No se encuentra %s" % TM_IDS_PATH)
        return

    tm_ids = json.loads(TM_IDS_PATH.read_text(encoding="utf-8"))
    log("%d equipos cargados" % len(tm_ids))

    injuries_all = {}
    if INJURIES_PATH.exists():
        try:
            injuries_all = json.loads(INJURIES_PATH.read_text(encoding="utf-8"))
            log("Cargados %d equipos en injuries.json" % len(injuries_all))
        except:
            pass

    tm_stats_all = {}
    if TM_STATS_PATH.exists():
        try:
            tm_stats_all = json.loads(TM_STATS_PATH.read_text(encoding="utf-8"))
            log("Cargados %d equipos en transfermarkt_stats.json" % len(tm_stats_all))
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
            tm_id = tm_ids[slug]
            log("[%d/%d]" % (i, len(slugs)))

            t0 = time.time()
            data = await scrape_team(context, slug, tm_id)
            elapsed = time.time() - t0

            injuries_all[slug] = {"injuries": data["injuries"]}
            tm_stats_all[slug] = {
                "team": data["team"],
                "slug": slug,
                "tm_id": tm_id,
                "market_value": data["market_value"],
                "average_age": data["average_age"],
                "squad_size": data["squad_size"],
                "manager": data.get("manager", ""),
            }

            log("  Hecho en %.1fs" % elapsed)

            INJURIES_PATH.write_text(json.dumps(injuries_all, ensure_ascii=False, indent=2), encoding="utf-8")
            TM_STATS_PATH.write_text(json.dumps(tm_stats_all, ensure_ascii=False, indent=2), encoding="utf-8")

            await asyncio.sleep(2)

        await browser.close()

    log("=" * 60)
    injured_count = sum(1 for v in injuries_all.values() if v.get("injuries"))
    log("COMPLETADO: %d/%d equipos con lesiones" % (injured_count, len(slugs)))
    log("injuries.json: %s" % INJURIES_PATH)
    log("transfermarkt_stats.json: %s" % TM_STATS_PATH)
    log("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
