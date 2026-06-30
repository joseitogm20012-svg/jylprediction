# ScrapyCoco: Scrapers para Mercados Secundarios — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir 4 nuevos scrapers a ScrapyCoco (shooting, passing, keepers, corners) que alimenten los mercados secundarios de predecirv2, y mejorar el scraper existente de Transfermarkt con datos de lesiones.

**Architecture:** Cada nuevo scraper es un script Python standalone en `data/` (estilo `fetch_fbref_cards.py`), invocado por `FBrefScraper` en ScrapyCoco como subproceso. Los scripts usan `soccerdata` + `beautifulsoup4` para extraer tablas de FBref, normalizan nombres de equipo vía `FBREF_NAME_TO_SLUG`. Datos por equipo se mergean en `xg_by_team.json`; datos por jugador se escriben a `data/player_stats.json`. Transfermarkt se mejora añadiendo scraping de tabla de lesiones.

**Tech Stack:** Python 3.12+, requests, beautifulsoup4, soccerdata, playwright (Transfermarkt)

## Global Constraints

- Seguir el patrón exacto de los scripts existentes: `fetch_fbref_xg.py`, `fetch_fbref_cards.py`
- No añadir dependencias nuevas — usar solo `requests`, `beautifulsoup4`, `soccerdata`
- Mantener encoding UTF-8 y slug mapping consistente (FBREF_NAME_TO_SLUG)
- Datos por equipo (`corners`) se mergean a `data/xg_by_team.json`
- Datos por jugador (`shooting`, `passing`, `keepers`) se escriben a `data/player_stats.json`
- ScrapyCoco está en `scrapycoco/`; los scripts de datos están en `data/`
- Registrar cada nuevo scraper en `scrapycoco/main.py` en el dict `SCRAPERS`

---

### Task 1: `fetch_fbref_shooting.py` — Estadísticas de Tiros por Jugador

**Files:**
- Create: `data/fetch_fbref_shooting.py`
- Modify: `scrapycoco/main.py:58-84` (registrar nuevo scraper)

**Interfaces:**
- Consumes: `FBREF_NAME_TO_SLUG` (hardcoded, mismo que `fetch_fbref_cards.py`)
- Produces: `data/player_stats.json` con estructura `{slug: {shooting: [{player, shots, shots_on_target, goals, header_goals, ...}]}}`

**Output format in `player_stats.json`:**
```json
{
  "argentina": {
    "shooting": [
      {"player": "Lionel Messi", "shots": 45, "shots_on_target": 22, "goals": 8, 
       "header_goals": 0, "shots_per_90": 3.2, "goals_per_90": 0.6, "g_per_shot": 0.18}
    ]
  }
}
```

- [ ] **Step 1: Leer `fetch_fbref_cards.py` como plantilla**

Estudiar la estructura: imports, FBREF_NAME_TO_SLUG, carga de `xg_by_team.json`, scraping con `soccerdata`, merge de datos.

- [ ] **Step 2: Escribir el script**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obtiene estadísticas de TIROS por jugador desde FBref (Mundiales 2018, 2022, 2026).
Escribe en data/player_stats.json bajo la clave 'shooting'.

Campos por jugador:
    - player: nombre del jugador
    - shots: tiros totales
    - shots_on_target: tiros a puerta
    - goals: goles
    - header_goals: goles de cabeza
    - shots_per_90: tiros por 90 min
    - goals_per_90: goles por 90 min
    - g_per_shot: goles por tiro
    - team_slug: slug del equipo
"""
import json, sys, io, os
from pathlib import Path
from bs4 import BeautifulSoup
import requests

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
PLAYER_STATS_PATH = BASE_DIR / "player_stats.json"

FBREF_NAME_TO_SLUG = { /* mismo mapping que fetch_fbref_cards.py */ }

WORLD_CUP_IDS = {"2018": 13, "2022": 133, "2026": 166}

def fetch_shooting_for_team(team_name: str) -> list[dict]:
    """
    Para cada Mundial, busca la página de shooting stats y extrae datos del equipo.
    Retorna lista de dicts con stats por jugador.
    """
    players = []
    for year, comp_id in WORLD_CUP_IDS.items():
        url = f"https://fbref.com/en/comps/{comp_id}/shooting/World-Cup-Shooting-Stats"
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            soup = BeautifulSoup(resp.content, "html.parser")
            table = soup.find("table", id="stats_shooting")
            if not table:
                # try partial match
                table = soup.find("table", {"id": lambda x: x and "stats_shooting" in x})
            if not table:
                continue
            tbody = table.find("tbody")
            if not tbody:
                continue
            for row in tbody.find_all("tr"):
                team_el = row.find("td", {"data-stat": "team"})
                if not team_el:
                    continue
                row_team = team_el.get_text(strip=True)
                if row_team.lower() != team_name.lower():
                    continue
                player_el = row.find("th", {"data-stat": "player"})
                if not player_el:
                    continue
                player_name = player_el.get_text(strip=True)
                def g(stat):
                    el = row.find("td", {"data-stat": stat})
                    return el.get_text(strip=True) if el else "0"
                players.append({
                    "player": player_name,
                    "shots": g("shots_total"),
                    "shots_on_target": g("shots_on_target"),
                    "goals": g("goals"),
                    "header_goals": g("goals_header"),
                    "shots_per_90": g("shots_per_90"),
                    "goals_per_90": g("goals_per_90"),
                    "g_per_shot": g("goals_per_shot"),
                })
        except Exception as e:
            print(f"[WARN] Error fetching shooting stats for {team_name} ({year}): {e}")
    return players

def main():
    print("=" * 60)
    print("  FBref Shooting Stats Scraper")
    print("=" * 60)
    
    all_data = {}
    if PLAYER_STATS_PATH.exists():
        try:
            all_data = json.loads(PLAYER_STATS_PATH.read_text(encoding="utf-8"))
            print(f"Datos existentes cargados: {len(all_data)} equipos")
        except:
            all_data = {}
    
    for fbref_name, slug in FBREF_NAME_TO_SLUG.items():
        print(f"Procesando {fbref_name} ({slug})...")
        players = fetch_shooting_for_team(fbref_name)
        if slug not in all_data:
            all_data[slug] = {}
        all_data[slug]["shooting"] = players
        print(f"  → {len(players)} jugadores")
    
    PLAYER_STATS_PATH.write_text(
        json.dumps(all_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\nDatos guardados en {PLAYER_STATS_PATH}")
    print(f"Total equipos: {len(all_data)}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Verificar que el script corre sin errores**

Run: `python data/fetch_fbref_shooting.py`
Expected: Logs de progreso, archivo `data/player_stats.json` creado con estructura válida.

- [ ] **Step 4: Registrar en ScrapyCoco**

Añadir en `scrapycoco/main.py` dentro de `SCRAPERS`:
```python
    "shooting": {
        "name": "Tiros por Jugador (FBref - Shooting)",
        "description": "Scrapea estadísticas de tiros, tiros a puerta y goles de cabeza por jugador desde FBref.",
        "script": "data/fetch_fbref_shooting.py"
    },
```

- [ ] **Step 5: Commit**

```bash
git add data/fetch_fbref_shooting.py scrapycoco/main.py
git commit -m "feat(scrapycoco): add shooting stats scraper per player"
```

---

### Task 2: `fetch_fbref_passing.py` — Estadísticas de Pases y Asistencias por Jugador

**Files:**
- Create: `data/fetch_fbref_passing.py`
- Modify: `scrapycoco/main.py:58-84`

**Interfaces:**
- Consumes: `FBREF_NAME_TO_SLUG`
- Produces: `data/player_stats.json` → `{slug: {passing: [{player, assists, key_passes, passes_completed, ...}]}}`

**Output:**
```json
{
  "argentina": {
    "passing": [
      {"player": "Lionel Messi", "assists": 5, "key_passes": 18, "passes_completed": 312,
       "passes_attempted": 380, "pass_pct": 82.1, "assists_per_90": 0.4}
    ]
  }
}
```

- [ ] **Step 1: Escribir `data/fetch_fbref_passing.py`**

Mismo patrón que `fetch_fbref_shooting.py`, pero scrapeando la tabla `stats_passing` de FBref. Extraer: `assists`, `passes_completed`, `passes` (attempted), `pass_pct`, `key_passes`, `assists_per_90`.

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obtiene estadísticas de PASES y ASISTENCIAS por jugador desde FBref.
Escribe en data/player_stats.json bajo la clave 'passing'.

Campos por jugador:
    - player: nombre
    - assists: asistencias
    - key_passes: pases clave
    - passes_completed: pases completados
    - passes_attempted: pases intentados
    - pass_pct: porcentaje de acierto
    - assists_per_90: asistencias por 90 min
    - team_slug: slug del equipo
"""
import json, sys, io
from pathlib import Path
from bs4 import BeautifulSoup
import requests

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
PLAYER_STATS_PATH = BASE_DIR / "player_stats.json"

FBREF_NAME_TO_SLUG = { /* copiar de fetch_fbref_cards.py */ }

WORLD_CUP_IDS = {"2018": 13, "2022": 133, "2026": 166}

def fetch_passing_for_team(team_name: str) -> list[dict]:
    players = []
    for year, comp_id in WORLD_CUP_IDS.items():
        url = f"https://fbref.com/en/comps/{comp_id}/passing/World-Cup-Passing-Stats"
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            soup = BeautifulSoup(resp.content, "html.parser")
            table = soup.find("table", id="stats_passing")
            if not table:
                continue
            tbody = table.find("tbody")
            if not tbody:
                continue
            for row in tbody.find_all("tr"):
                team_el = row.find("td", {"data-stat": "team"})
                if not team_el or team_el.get_text(strip=True).lower() != team_name.lower():
                    continue
                player_el = row.find("th", {"data-stat": "player"})
                if not player_el:
                    continue
                def g(stat):
                    el = row.find("td", {"data-stat": stat})
                    return el.get_text(strip=True) if el else "0"
                players.append({
                    "player": player_el.get_text(strip=True),
                    "assists": g("assists"),
                    "key_passes": g("passes_1_3"),
                    "passes_completed": g("passes_completed"),
                    "passes_attempted": g("passes"),
                    "pass_pct": g("pass_pct"),
                    "assists_per_90": g("assists_per_90"),
                })
        except Exception as e:
            print(f"[WARN] Error fetching passing stats for {team_name} ({year}): {e}")
    return players

def main():
    print("=" * 60)
    print("  FBref Passing Stats Scraper")
    print("=" * 60)
    all_data = {}
    if PLAYER_STATS_PATH.exists():
        try:
            all_data = json.loads(PLAYER_STATS_PATH.read_text(encoding="utf-8"))
        except:
            all_data = {}
    for fbref_name, slug in FBREF_NAME_TO_SLUG.items():
        print(f"Procesando {fbref_name} ({slug})...")
        players = fetch_passing_for_team(fbref_name)
        if slug not in all_data:
            all_data[slug] = {}
        all_data[slug]["passing"] = players
        print(f"  → {len(players)} jugadores")
    PLAYER_STATS_PATH.write_text(json.dumps(all_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Datos guardados en {PLAYER_STATS_PATH}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verificar que el script corre sin errores**

Run: `python data/fetch_fbref_passing.py`
Expected: `data/player_stats.json` actualizado con clave `passing` por equipo.

- [ ] **Step 3: Registrar en ScrapyCoco**

```python
    "passing": {
        "name": "Asistencias y Pases (FBref - Passing)",
        "description": "Scrapea asistencias, pases clave y precisión de pases por jugador desde FBref.",
        "script": "data/fetch_fbref_passing.py"
    },
```

- [ ] **Step 4: Commit**

```bash
git add data/fetch_fbref_passing.py scrapycoco/main.py
git commit -m "feat(scrapycoco): add passing stats scraper per player"
```

---

### Task 3: `fetch_fbref_keepers.py` — Estadísticas de Porteros por Jugador

**Files:**
- Create: `data/fetch_fbref_keepers.py`
- Modify: `scrapycoco/main.py:58-84`

**Interfaces:**
- Consumes: `FBREF_NAME_TO_SLUG`
- Produces: `data/player_stats.json` → `{slug: {keepers: [{player, clean_sheets, saves, goals_against, ...}]}}`

**Output:**
```json
{
  "argentina": {
    "keepers": [
      {"player": "Emiliano Martínez", "clean_sheets": 4, "saves": 18, "goals_against": 5,
       "saves_per_90": 2.8, "goals_against_per_90": 0.8, "save_pct": 78.3}
    ]
  }
}
```

- [ ] **Step 1: Escribir `data/fetch_fbref_keepers.py`**

Scrapea tabla `stats_keeper` de FBref. Mismo patrón que los anteriores.

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obtiene estadísticas de PORTEROS por jugador desde FBref.
Escribe en data/player_stats.json bajo la clave 'keepers'.
"""
import json, sys, io
from pathlib import Path
from bs4 import BeautifulSoup
import requests

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
PLAYER_STATS_PATH = BASE_DIR / "player_stats.json"
FBREF_NAME_TO_SLUG = { /* copiar */ }
WORLD_CUP_IDS = {"2018": 13, "2022": 133, "2026": 166}

def fetch_keepers_for_team(team_name: str) -> list[dict]:
    players = []
    for year, comp_id in WORLD_CUP_IDS.items():
        url = f"https://fbref.com/en/comps/{comp_id}/keepers/World-Cup-Goalkeeping-Stats"
        try:
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            soup = BeautifulSoup(resp.content, "html.parser")
            table = soup.find("table", id="stats_keeper")
            if not table:
                continue
            tbody = table.find("tbody")
            if not tbody:
                continue
            for row in tbody.find_all("tr"):
                team_el = row.find("td", {"data-stat": "team"})
                if not team_el or team_el.get_text(strip=True).lower() != team_name.lower():
                    continue
                player_el = row.find("th", {"data-stat": "player"})
                if not player_el:
                    continue
                def g(stat):
                    el = row.find("td", {"data-stat": stat})
                    return el.get_text(strip=True) if el else "0"
                players.append({
                    "player": player_el.get_text(strip=True),
                    "clean_sheets": g("clean_sheets"),
                    "saves": g("saves"),
                    "goals_against": g("goals_against"),
                    "saves_per_90": g("saves_per_90"),
                    "goals_against_per_90": g("goals_against_per_90"),
                    "save_pct": g("save_pct"),
                })
        except Exception as e:
            print(f"[WARN] Error fetching keeper stats for {team_name} ({year}): {e}")
    return players

def main():
    print("=" * 60)
    print("  FBref Goalkeeping Stats Scraper")
    print("=" * 60)
    all_data = {}
    if PLAYER_STATS_PATH.exists():
        try:
            all_data = json.loads(PLAYER_STATS_PATH.read_text(encoding="utf-8"))
        except:
            all_data = {}
    for fbref_name, slug in FBREF_NAME_TO_SLUG.items():
        print(f"Procesando {fbref_name} ({slug})...")
        players = fetch_keepers_for_team(fbref_name)
        if slug not in all_data:
            all_data[slug] = {}
        all_data[slug]["keepers"] = players
        print(f"  → {len(players)} jugadores")
    PLAYER_STATS_PATH.write_text(json.dumps(all_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Datos guardados en {PLAYER_STATS_PATH}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verificar que el script corre sin errores**

Run: `python data/fetch_fbref_keepers.py`
Expected: `player_stats.json` actualizado con clave `keepers`.

- [ ] **Step 3: Registrar en ScrapyCoco**

```python
    "keepers": {
        "name": "Porteros (FBref - Goalkeeping)",
        "description": "Scrapea estadísticas de porteros: vallas invictas, atajadas, goles recibidos desde FBref.",
        "script": "data/fetch_fbref_keepers.py"
    },
```

- [ ] **Step 4: Commit**

```bash
git add data/fetch_fbref_keepers.py scrapycoco/main.py
git commit -m "feat(scrapycoco): add goalkeeper stats scraper per player"
```

---

### Task 4: `fetch_fbref_corners.py` — Estadísticas de Córners por Equipo

**Files:**
- Create: `data/fetch_fbref_corners.py`
- Modify: `scrapycoco/main.py:58-84`

**Interfaces:**
- Consumes: `FBREF_NAME_TO_SLUG`
- Produces: `data/xg_by_team.json` añadiendo campos `corners_per_90`, `corners_for`, `corners_against` a cada equipo

**Output (mergeado en `xg_by_team.json`):**
```json
{
  "argentina": {
    "xg_overall": 2.1,
    "shots_per_90": 12.0,
    "corners_per_90": 5.2,
    "corners_for": 42,
    "corners_against": 28,
    ...
  }
}
```

- [ ] **Step 1: Escribir `data/fetch_fbref_corners.py`**

Scrapea la tabla de equipo (no jugador) de FBref que contiene estadísticas de córners. FBref incluye corners en la tabla `stats_team` o `stats_squads_standard`. Se puede obtener desde la página de "Team Stats" de cada Mundial.

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obtiene estadísticas de CÓRNERS por equipo desde FBref.
Mergea los datos en xg_by_team.json.

Campos añadidos a cada equipo:
    - corners_per_90: córners a favor por 90 min
    - corners_for: total córners a favor
    - corners_against: total córners en contra
"""
import json, sys, io
from pathlib import Path
from bs4 import BeautifulSoup
import requests

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
XG_PATH = BASE_DIR / "xg_by_team.json"

FBREF_NAME_TO_SLUG = { /* copiar de fetch_fbref_cards.py */ }

# Mapeo de nombre FBref a slugs para páginas de equipo
# corners aparecen en la tabla de "Squad Stats" por competición
WORLD_CUP_TEAM_URLS = {
    13: "https://fbref.com/en/comps/13/2018/stats/2018-World-Cup-Stats",
    133: "https://fbref.com/en/comps/133/2022/stats/2022-World-Cup-Stats",
    166: "https://fbref.com/en/comps/166/2026/stats/2026-World-Cup-Stats",
}

def fetch_corners() -> dict[str, dict]:
    """Retorna {slug: {corners_per_90, corners_for, corners_against}}"""
    results = {}
    for comp_id, url in WORLD_CUP_TEAM_URLS.items():
        try:
            print(f"Scrapeando {url}...")
            resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            soup = BeautifulSoup(resp.content, "html.parser")
            table = soup.find("table", id="stats_squads_standard")
            if not table:
                continue
            tbody = table.find("tbody")
            if not tbody:
                continue
            for row in tbody.find_all("tr"):
                team_el = row.find("td", {"data-stat": "team"})
                if not team_el:
                    continue
                fbref_name = team_el.get_text(strip=True)
                slug = FBREF_NAME_TO_SLUG.get(fbref_name)
                if not slug:
                    continue
                def g(stat):
                    el = row.find("td", {"data-stat": stat})
                    return el.get_text(strip=True) if el else "0"
                if slug not in results:
                    results[slug] = {"corners_for": 0, "corners_against": 0, "matches": 0}
                # Intentar corner_kick (si existe en la tabla extendida)
                # Si no está en la tabla estándar, buscar en la tabla "stats_squads_keepers"
                # En su defecto, calcular desde "corners_taken"
                corners = g("corner_kicks")
                if corners == "0":
                    corners = g("corner_kicks_taken")
                try:
                    results[slug]["corners_for"] += int(corners) if corners.replace(",","").isdigit() else 0
                except:
                    pass
                matches = g("matches")
                try:
                    results[slug]["matches"] += int(matches) if matches.replace(",","").isdigit() else 0
                except:
                    pass
        except Exception as e:
            print(f"[WARN] Error fetching corners for comp {comp_id}: {e}")
    
    # Calcular per 90
    for slug, data in results.items():
        m = max(data["matches"], 1)
        data["corners_per_90"] = round(data["corners_for"] / m, 1)
        data.pop("matches", None)
    return results

def main():
    print("=" * 60)
    print("  FBref Corners Stats Scraper")
    print("=" * 60)
    
    # Cargar xg_by_team.json existente
    if not XG_PATH.exists():
        print(f"ERROR: {XG_PATH} no existe. Ejecutar fetch_fbref_xg.py primero.")
        sys.exit(1)
    
    xg_data = json.loads(XG_PATH.read_text(encoding="utf-8"))
    print(f"Datos existentes cargados: {len(xg_data)} equipos")
    
    corners = fetch_corners()
    print(f"Córners scrapeados: {len(corners)} equipos")
    
    # Mergear
    updated = 0
    for slug, cdata in corners.items():
        if slug in xg_data:
            xg_data[slug]["corners_per_90"] = cdata["corners_per_90"]
            xg_data[slug]["corners_for"] = cdata["corners_for"]
            xg_data[slug]["corners_against"] = cdata["corners_against"]
            updated += 1
    
    XG_PATH.write_text(json.dumps(xg_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Actualizados: {updated} equipos en {XG_PATH}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verificar que el script corre sin errores**

Run: `python data/fetch_fbref_corners.py`
Expected: `xg_by_team.json` actualizado con campos `corners_per_90`, `corners_for`, `corners_against`.

- [ ] **Step 3: Registrar en ScrapyCoco**

```python
    "corners": {
        "name": "Córners por Equipo (FBref)",
        "description": "Scrapea estadísticas de córners a favor y en contra por equipo desde FBref.",
        "script": "data/fetch_fbref_corners.py"
    },
```

- [ ] **Step 4: Commit**

```bash
git add data/fetch_fbref_corners.py scrapycoco/main.py
git commit -m "feat(scrapycoco): add corners stats scraper per team"
```

---

### Task 5: Mejorar Transfermarkt con Datos de Lesiones

**Files:**
- Modify: `scrapycoco/scrapers/transfermarkt.py`
- Modify: `scrapycoco/main.py:68-72`

**Interfaces:**
- Consumes: `team_name` (parámetro del scraper)
- Produces: Datos de lesiones guardados en `data/injuries.json` y mostrados en preview

**Output (`data/injuries.json`):**
```json
{
  "argentina": {
    "injuries": [
      {"player": "Lionel Messi", "injury": "Fatiga muscular", "return_date": "2026-07-05", "status": "Doubtful"},
      {"player": "Angel Di Maria", "injury": "", "status": "Fit"}
    ]
  }
}
```

- [ ] **Step 1: Leer `transfermarkt.py` completo**

Estudiar el flujo actual: búsqueda Google → navegación a perfil → extraer header (edad, entrenador, valor).

- [ ] **Step 2: Añadir scraping de tabla de lesiones**

Después de la extracción actual, navegar a la pestaña "injuries" o "suspensions" si existe. Transfermarkt tiene URL tipo `.../verletzungen/...` para lesiones.

Añadir después de la línea donde se parsea el header:

```python
# ── Scraping de lesiones ────────────────────────────────────────────────
injuries = []
try:
    # Intentar navegar a la página de lesiones
    injury_url = profile_url.replace("/startseite/", "/verletzungen/")
    self.log(f"Navegando a página de lesiones...")
    await page.goto(injury_url, timeout=20000)
    await asyncio.sleep(2)
    
    injury_table = await page.query_selector("table.items")
    if injury_table:
        rows = await injury_table.query_selector_all("tr:has(td)")
        for row in rows:
            tds = await row.query_selector_all("td")
            if len(tds) >= 3:
                player = (await tds[0].inner_text()).strip()
                injury = (await tds[1].inner_text()).strip()
                status = (await tds[2].inner_text()).strip()
                injuries.append({
                    "player": player,
                    "injury": injury,
                    "status": status
                })
        self.log(f"Lesiones encontradas: {len(injuries)}")
    else:
        self.log("No se encontró tabla de lesiones.")
except Exception as e:
    self.log(f"No se pudo obtener lesiones: {e}")

# Guardar en preview data
result = {
    "team": team_name,
    "average_age": avg_age,
    "coach": coach,
    "squad_value": squad_value,
    "injuries": injuries
}
self.set_preview_data([result])

# También guardar a disco
import json
injuries_path = Path(self.data_dir) / "injuries.json"
existing = {}
if injuries_path.exists():
    try:
        existing = json.loads(injuries_path.read_text(encoding="utf-8"))
    except:
        existing = {}
existing[team_name] = {"injuries": injuries}
injuries_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
```

- [ ] **Step 3: Verificar que el scraper corre sin errores**

Ejecutar TransfermarktScraper desde ScrapyCoco con `team_name=argentina`, modo sandbox=false.
Expected: Logs de navegación, preview data con lista de lesiones.

- [ ] **Step 4: Commit**

```bash
git add scrapycoco/scrapers/transfermarkt.py scrapycoco/main.py
git commit -m "feat(scrapycoco): add injury data scraping to Transfermarkt"
```

---

### Task 6: Validar Plan Completo y Testing de Integración

**Files:**
- Modify: Ninguno (solo verificación)

- [ ] **Step 1: Verificar que los 4 scripts existen y son ejecutables**

```bash
python data/fetch_fbref_shooting.py --dry-run
python data/fetch_fbref_passing.py --dry-run
python data/fbref_fetch_keepers.py --dry-run
python data/fetch_fbref_corners.py --dry-run
```

- [ ] **Step 2: Verificar que ScrapyCoco tiene los 4 nuevos scrapers registrados**

Revisar `scrapycoco/main.py` `SCRAPERS` que contenga: `shooting`, `passing`, `keepers`, `corners`.

- [ ] **Step 3: Iniciar ScrapyCoco y probar UI**

```bash
cd scrapycoco && python main.py
```
Abrir `http://localhost:3005`. Verificar que aparezcan 12 tarjetas de scraper en el grid.

- [ ] **Step 4: Commit final**

```bash
git add -A
git commit -m "feat: add 4 new FBref scrapers (shooting, passing, keepers, corners) + Transfermarkt injuries"
```

