"""
SCRAPEO MASIVO MUNDIAL 2026 - Todos los partidos
"""
import json, csv, asyncio, re, time
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

OUT_DIR = Path("C:/Users/Equipo/Desktop/mundial104")
OUT_DIR.mkdir(parents=True, exist_ok=True)
IDS_FILE = OUT_DIR / "all_match_ids.json"
PROGRESS_FILE = OUT_DIR / "progress.json"

MAX_WORKERS = 5  # Parallel browsers

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
]

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print("[%s] %s" % (ts, msg))

async def cookie_banner(page):
    try:
        btn = await page.query_selector("#onetrust-accept-btn-handler")
        if btn: await btn.click()
    except Exception: pass

async def click_secondary_tab_by_href(page, keyword):
    try:
        hrefs = await page.evaluate('''() => {
            const tabs = document.querySelectorAll('div[class*="tabsSecondary"] a[data-discover="true"]');
            const result = {};
            for (const a of tabs) {
                if (a.href) result[a.href] = a.textContent.trim();
            }
            return result;
        }''')
        for href, text in hrefs.items():
            if keyword.lower() in text.lower() or keyword.lower() in href.lower():
                await page.goto(href, timeout=30000, wait_until="domcontentloaded")
                await asyncio.sleep(3)
                return True
    except Exception as e:
        log("  Error tab nav: %s" % e)
    return False

async def scrape_team_stats(page) -> dict:
    stats = {}
    try:
        soup = BeautifulSoup(await page.content(), "html.parser")
        for row in soup.select("div[class*='wcl-row_']"):
            cat = row.select_one("div[class*='wcl-category_']")
            home = row.select_one("div[class*='wcl-homeValue_']")
            away = row.select_one("div[class*='wcl-awayValue_']")
            if cat and home and away:
                stats[cat.get_text().strip()] = {
                    "home": home.get_text().strip(),
                    "away": away.get_text().strip()
                }
    except Exception as e:
        log("  Error stats: %s" % e)
    return stats

def group_by_ancestor(els, depth):
    from collections import defaultdict
    groups = defaultdict(list)
    for el in els:
        name = el.get_text().strip()
        if not name:
            continue
        ancestors = list(el.parents)
        if len(ancestors) > depth:
            groups[id(ancestors[depth])].append(name)
    return [list(dict.fromkeys(g)) for g in groups.values()]

async def scrape_lineups(page) -> dict:
    lineups = {"local": {"titulares": [], "suplentes": [], "formacion": ""},
               "visitante": {"titulares": [], "suplentes": [], "formacion": ""}}
    try:
        soup = BeautifulSoup(await page.content(), "html.parser")

        players = soup.select("*[class*='lineupsParticipantName']")
        if players:
            groups = group_by_ancestor(players, 3)
            groups.sort(key=len, reverse=True)
            team_groups = [g for g in groups if len(g) >= 4][:2]
            if len(team_groups) >= 2:
                lineups["local"]["titulares"] = team_groups[0]
                lineups["visitante"]["titulares"] = team_groups[1]

        for el in soup.select("*[class*='formation']"):
            t = el.get_text().strip()
            m = re.match(r'^(\d[\d\s-]*)', t)
            if m:
                if not lineups["local"]["formacion"]:
                    lineups["local"]["formacion"] = m.group(1)
                elif not lineups["visitante"]["formacion"]:
                    lineups["visitante"]["formacion"] = m.group(1)
                    break

        sub_name_els = soup.select("*[class*='wcl-substitute'] button[class*='nameWrapper']")
        if sub_name_els:
            sub_groups = group_by_ancestor(sub_name_els, 4)
            sub_groups.sort(key=len, reverse=True)
            team_subs = [g for g in sub_groups if len(g) >= 2][:2]
            if len(team_subs) >= 2:
                lineups["local"]["suplentes"] = team_subs[0]
                lineups["visitante"]["suplentes"] = team_subs[1]
    except Exception as e:
        log("  Error lineups: %s" % e)
    return lineups

async def scrape_one_match(mid: str, browser) -> dict:
    base_url = "https://www.flashscore.es/partido/%s/" % mid
    page = await browser.new_page()
    result = {"match_id": mid, "estadisticas": {}, "alineaciones": {}, "error": None}
    try:
        await page.goto(base_url, timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        await cookie_banner(page)

        html = (await page.content()).lower()
        if not any(x in html for x in ["mundial", "world cup", "worldcup", "campeonato del mundo"]):
            result["error"] = "No es Mundial"
            return result

        try:
            desc = await page.query_selector("div[class*='duelParticipant'],div[class*='participant']")
            result["description"] = (await desc.text_content()).strip() if desc else (await page.title())
        except: result["description"] = ""
        try:
            sw = await page.query_selector("div[class*='detailScore__wrapper']")
            result["score"] = (await sw.text_content()).strip() if sw else ""
        except: result["score"] = ""

        if await click_secondary_tab_by_href(page, "estadisticas"):
            result["estadisticas"] = await scrape_team_stats(page)

        if await click_secondary_tab_by_href(page, "alineaciones"):
            result["alineaciones"] = await scrape_lineups(page)

        n_s = len(result["estadisticas"])
        al = result.get("alineaciones", {})
        n_lt = len(al.get("local", {}).get("titulares", []))
        n_vt = len(al.get("visitante", {}).get("titulares", []))
        log("  OK %s: %s | %d stats | %d vs %d" % (mid, result.get("score", "?"), n_s, n_lt, n_vt))
    except Exception as e:
        result["error"] = str(e)
        log("  ERR %s: %s" % (mid, e))
    finally:
        await page.close()
    return result

def save_match(result: dict):
    mid = result["match_id"]
    with open(OUT_DIR / ("%s.json" % mid), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    with open(OUT_DIR / ("%s.csv" % mid), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["# PARTIDO", result.get("description", "")])
        w.writerow(["# ID", mid])
        w.writerow(["# Tipo", "finalizado"])
        w.writerow(["# Ultima actualizacion", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]])
        w.writerow(["# RESULTADO", result.get("score", "")])
        w.writerow([])
        stats = result.get("estadisticas", {})
        if stats:
            w.writerow(["# === ESTADISTICAS ==="])
            w.writerow(["Categoria", "Local", "Visitante"])
            for cat, vals in sorted(stats.items(), key=lambda x: x[0]):
                w.writerow([cat, vals.get("home", ""), vals.get("away", "")])
            w.writerow([])
        al = result.get("alineaciones", {})
        if al:
            w.writerow(["# === ALINEACIONES (CONFIRMADA) ==="])
            for side in ["local", "visitante"]:
                sd = al.get(side, {})
                w.writerow(["# %s (formacion: %s)" % (side.upper(), sd.get("formacion", ""))])
                if sd.get("titulares"):
                    w.writerow(["# TITULARES"])
                    for p in sd["titulares"]:
                        w.writerow([p])
                if sd.get("suplentes"):
                    w.writerow(["# SUPLENTES"])
                    for p in sd["suplentes"]:
                        w.writerow([p])
                w.writerow([])

async def worker(worker_id, browser, match_ids, progress):
    for mid in match_ids:
        if mid in progress["done"]:
            log("[W%d] %s: ya procesado, saltando." % (worker_id, mid))
            continue
        log("[W%d] %s: comenzando..." % (worker_id, mid))
        result = await scrape_one_match(mid, browser)
        if result and result.get("error") != "No es Mundial":
            save_match(result)
            progress["done"].append(mid)
        else:
            progress["skipped"].append(mid)
        progress["total_processed"] += 1

async def main():
    log("=" * 60)
    log("SCRAPEO MASIVO MUNDIAL 2026")
    log("=" * 60)

    with open(IDS_FILE) as f:
        all_ids = json.load(f)
    log("Total IDs a procesar: %d" % len(all_ids))

    progress = {"done": [], "skipped": [], "total_processed": 0}
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            saved = json.load(f)
            for k in saved:
                progress[k] = saved[k]
        log("Progreso recuperado: %d hechos, %d saltados" % (len(progress["done"]), len(progress["skipped"])))

    remaining = [mid for mid in all_ids if mid not in progress["done"] and mid not in progress["skipped"]]
    log("Restantes: %d" % len(remaining))

    if not remaining:
        log("Todo completado!")
        return

    t0 = time.time()
    async with async_playwright() as p:
        browsers = []
        for i in range(MAX_WORKERS):
            b = await p.chromium.launch(headless=True)
            browsers.append(b)

        chunks = [[] for _ in range(MAX_WORKERS)]
        for i, mid in enumerate(remaining):
            chunks[i % MAX_WORKERS].append(mid)

        tasks = []
        for i in range(MAX_WORKERS):
            tasks.append(worker(i, browsers[i], chunks[i], progress))

        await asyncio.gather(*tasks)

        for b in browsers:
            await b.close()

    elapsed = time.time() - t0
    log("=" * 60)
    log("COMPLETADO en %.1f min" % (elapsed / 60))
    log("Procesados: %d | Hechos: %d | Saltados: %d" % (
        progress["total_processed"], len(progress["done"]), len(progress["skipped"])))

    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)

    stats_total = 0
    lineups_total = 0
    for mid in progress["done"]:
        fpath = OUT_DIR / ("%s.json" % mid)
        if fpath.exists():
            with open(fpath) as f:
                d = json.load(f)
            stats_total += len(d.get("estadisticas", {}))
            al = d.get("alineaciones", {})
            lt = len(al.get("local", {}).get("titulares", []))
            vt = len(al.get("visitante", {}).get("titulares", []))
            lineups_total += lt + vt

    completed = len(progress["done"])
    log("\nResumen final:")
    log("  Partidos completados: %d" % completed)
    log("  Promedio stats/partido: %.1f" % (stats_total / completed if completed else 0))
    log("  Promedio titulares/partido: %.1f" % (lineups_total / completed if completed else 0))

if __name__ == "__main__":
    asyncio.run(main())
