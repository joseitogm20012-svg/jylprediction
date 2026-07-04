"""
SCRAPEO v2 — LESIONES + METADATA DE TRANSFERMARKT
Usa IDs conocidos de TM. Sin Google, sin Playwright.
"""
import json, re, time, sys
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

TM_IDS_PATH = Path(__file__).parent / "wc2026_tm_ids.json"
OUT_DIR = Path("C:/Users/Equipo/Desktop/predecirv2/data")
OUT_DIR.mkdir(parents=True, exist_ok=True)
INJURIES_PATH = OUT_DIR / "injuries.json"
TM_STATS_PATH = OUT_DIR / "transfermarkt_stats.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

log_lines = []

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print("[%s] %s" % (ts, msg))
    log_lines.append("[%s] %s" % (ts, msg))

def fetch(url, label, retries=3):
    for attempt in range(1, retries + 1):
        try:
            r = SESSION.get(url, timeout=20)
            if r.status_code == 200:
                return r.text
            log("  %s: HTTP %d (attempt %d/%d)" % (label, r.status_code, attempt, retries))
        except requests.RequestException as e:
            log("  %s: %s (attempt %d/%d)" % (label, e, attempt, retries))
        if attempt < retries:
            time.sleep(3 * attempt)
    return None

def parse_squad_page(html, slug, team_display):
    result = {"market_value": "", "average_age": "", "squad_size": "", "manager": ""}
    soup = BeautifulSoup(html, "html.parser")

    # Market value from header
    header = soup.find(class_="data-header")
    if header:
        for span in header.find_all("span", class_="data-header__label"):
            text = span.get_text(strip=True)
            val_el = span.find(class_="data-header__content")
            if not val_el:
                val_el = span.find("a")
            if not val_el:
                continue
            val = val_el.get_text(strip=True)
            if "Average age" in text or "Edad media" in text or "Durchschnittsalter" in text:
                result["average_age"] = val
            if "Coach" in text or "Manager" in text or "Entrenador" in text or "Trainer" in text:
                result["manager"] = val
            if "Squad size" in text or "Kadergröße" in text or "Jugadores" in text:
                result["squad_size"] = val

        # Market value from the big value box
        value_div = header.find(class_="data-header__market-value")
        if value_div:
            result["market_value"] = value_div.get_text(strip=True)

    # Also try finding market value in other ways
    if not result["market_value"]:
        # Look for the total market value in the info box
        m = re.search(r'(?:Total market value|Gesamtmarktwert|Valor de mercado total)[:\s]*([\d.,]+\s*(?:mio|mill|Mio|€|m|M)[\d.,\s]*(?:€|Mio\.)?)', html, re.IGNORECASE)
        if m:
            result["market_value"] = m.group(1).strip()

    # Parse detailed-info-table (common in squad page)
    info_table = soup.find("table", class_="details-table-content")
    if not info_table:
        info_table = soup.find("div", class_="detail-content-wrap")
    if info_table:
        all_text = info_table.get_text(" | ", strip=True)
        for line in all_text.split(" | "):
            low = line.lower()
            if "average age" in low or "edad media" in low or "durchschnittsalter" in low:
                result["average_age"] = line.split(":")[-1].strip() if ":" in line else ""
            if "squad size" in low or "kadergröße" in low:
                result["squad_size"] = line.split(":")[-1].strip() if ":" in line else ""

    # Try to find manager from div.profilname or similar
    if not result["manager"]:
        for a in soup.find_all("a", href=lambda h: h and "trainer" in h.lower()):
            result["manager"] = a.get_text(strip=True)
            break
    if not result["manager"]:
        for a in soup.find_all("a", href=lambda h: h and "/mitarbeiter" in h):
            txt = a.get_text(strip=True)
            if txt and txt != slug:
                result["manager"] = txt
                break

    return result

def parse_injuries_page(html):
    injuries = []
    soup = BeautifulSoup(html, "html.parser")
    itable = soup.find("table", class_="items")
    if itable:
        for tr in itable.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) >= 3:
                player = tds[0].get_text(strip=True)
                injury = tds[1].get_text(strip=True)
                status = tds[2].get_text(strip=True)
                if player and injury:
                    injuries.append({"player": player, "injury": injury, "status": status})
    return injuries

def scrape_team(slug, tm_id):
    team_display = slug.replace("-", " ").title()
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
    team_display = overrides.get(slug, team_display)

    log(">>> %s (ID %d)" % (team_display, tm_id))

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

    # Squad page
    squad_url = "https://www.transfermarkt.com/%s/startseite/verein/%d" % (slug, tm_id)
    html = fetch(squad_url, "%s squad" % slug)
    if html:
        squad_data = parse_squad_page(html, slug, team_display)
        result.update(squad_data)
        log("  Valor: %s | Edad: %s | Plantilla: %s | DT: %s" % (
            squad_data["market_value"] or "?",
            squad_data["average_age"] or "?",
            squad_data["squad_size"] or "?",
            squad_data["manager"] or "?",
        ))
    else:
        log("  No se pudo obtener pagina del equipo")
        result["error"] = "Squad page fetch failed"

    # Injuries page
    injury_url = "https://www.transfermarkt.com/%s/verletzungen/verein/%d" % (slug, tm_id)
    log("  Lesiones URL: %s" % injury_url)
    html = fetch(injury_url, "%s injuries" % slug)
    if html:
        injuries = parse_injuries_page(html)
        result["injuries"] = injuries
        log("  Lesiones: %d" % len(injuries))
    else:
        log("  No se pudo obtener pagina de lesiones")

    return result

def main():
    log("=" * 60)
    log("SCRAPEO v2 — LESIONES + METADATA TM")
    log("=" * 60)

    if not TM_IDS_PATH.exists():
        log("ERROR: No se encuentra %s" % TM_IDS_PATH)
        sys.exit(1)

    tm_ids = json.loads(TM_IDS_PATH.read_text(encoding="utf-8"))
    log("%d equipos cargados" % len(tm_ids))

    # Load existing data
    injuries_all = {}
    if INJURIES_PATH.exists():
        try:
            injuries_all = json.loads(INJURIES_PATH.read_text(encoding="utf-8"))
            log("Cargados %d equipos existentes en injuries.json" % len(injuries_all))
        except:
            pass

    tm_stats_all = {}
    if TM_STATS_PATH.exists():
        try:
            tm_stats_all = json.loads(TM_STATS_PATH.read_text(encoding="utf-8"))
            log("Cargados %d equipos existentes en transfermarkt_stats.json" % len(tm_stats_all))
        except:
            pass

    slugs = list(tm_ids.keys())
    for i, slug in enumerate(slugs, 1):
        tm_id = tm_ids[slug]
        log("[%d/%d]" % (i, len(slugs)))

        t0 = time.time()
        data = scrape_team(slug, tm_id)
        elapsed = time.time() - t0

        # Save injuries
        injuries_all[slug] = {"injuries": data["injuries"]}

        # Save TM stats
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

        # Save after each team
        INJURIES_PATH.write_text(json.dumps(injuries_all, ensure_ascii=False, indent=2), encoding="utf-8")
        TM_STATS_PATH.write_text(json.dumps(tm_stats_all, ensure_ascii=False, indent=2), encoding="utf-8")

        # Rate limiting
        time.sleep(2.5)

    log("=" * 60)
    injured_count = sum(1 for v in injuries_all.values() if v.get("injuries"))
    log("COMPLETADO: %d/%d equipos con lesiones" % (injured_count, len(slugs)))
    log("injuries.json: %s" % INJURIES_PATH)
    log("transfermarkt_stats.json: %s" % TM_STATS_PATH)
    log("=" * 60)

if __name__ == "__main__":
    main()
