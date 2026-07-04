import json
import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path
from difflib import SequenceMatcher
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from .base import BaseScraper


class FlashscoreScraper(BaseScraper):
    """
    Scraper robusto para Flashscore usando Playwright.
    Busca por nombre de partido (ej: 'Argentina vs Uruguay') o selección (ej: 'Argentina').

    Partidos FINALIZADOS:
      - Estadísticas del partido (posesión, tiros, etc.)
      - Alineaciones titulares + suplentes + formación
      - Estadísticas individuales de cada jugador

    Partidos FUTUROS:
      - Detecta si faltan <1 h para el inicio (alineación confirmada) o >1 h (alineación probable)
      - Alineaciones + suplentes + formación
      - Cuotas 1X2 de todas las casas de apuestas disponibles
    """

    # ── Helpers de extracción ──────────────────────────────────────────────

    async def _cookie_banner(self, page):
        """Cierra el banner de cookies si aparece."""
        try:
            btn = await page.query_selector("#onetrust-accept-btn-handler")
            if btn:
                await btn.click()
                await asyncio.sleep(1)
        except Exception:
            pass

    async def _click_tab(self, page, tab_texts) -> bool:
        """Hace clic en una pestaña por su texto (acepta lista de variantes). Retorna True si existía."""
        if isinstance(tab_texts, str):
            tab_texts = [tab_texts]
        for text in tab_texts:
            try:
                tab = page.locator("button").filter(has_text=text).first
                if await tab.is_visible():
                    await tab.click()
                    await asyncio.sleep(1.5)
                    return True
            except Exception:
                continue
        return False

    def _text(self, el, default=""):
        return el.get_text().strip() if el else default

    async def _soup(self, page):
        content = await page.content()
        return BeautifulSoup(content, "html.parser")

    # ── Búsqueda del equipo en Flashscore ──────────────────────────────────

    async def find_team_base_url(self, page, team_name: str) -> str:
        self.log(f"Buscando selección '{team_name}' en Flashscore...")
        await page.goto("https://www.flashscore.es/", timeout=30000)
        await asyncio.sleep(2)
        await self._cookie_banner(page)

        search_btn = await page.query_selector(".searchIcon")
        if not search_btn:
            self.log("No se encontró el botón de búsqueda en Flashscore.")
            return ""

        await search_btn.click()
        await asyncio.sleep(1)

        inputs = await page.query_selector_all("input")
        search_input = None
        for inp in inputs:
            if await inp.is_visible():
                search_input = inp
                break
        if not search_input:
            self.log("No se encontró el campo de texto de búsqueda.")
            return ""

        await search_input.fill(team_name)
        await asyncio.sleep(3)

        try:
            await asyncio.sleep(1)

            def _find_best_match(texts, query):
                """Find best fuzzy match among a list of texts."""
                best, best_ratio = None, 0
                for t in texts:
                    ratio = SequenceMatcher(None, query.lower(), t.lower()).ratio()
                    if ratio > best_ratio and ratio >= 0.45:
                        best, best_ratio = t, ratio
                return best, best_ratio

            participant = None
            # Strategy 1: exact match via Playwright locators
            search_selectors = [
                page.locator("div[class*='searchResult'] .searchResult__participantName").filter(has_text=team_name).first,
                page.locator("div[class*='searchResult'] a[class*='participantName']").filter(has_text=team_name).first,
                page.locator("div[class*='searchResult']").filter(has_text=team_name).first,
            ]
            for loc in search_selectors:
                try:
                    if await loc.is_visible(timeout=2000):
                        participant = loc
                        self.log(f"Coincidencia exacta encontrada para '{team_name}'.")
                        break
                except Exception:
                    continue

            if not participant:
                # Strategy 2: exact match via broad dialog selector
                try:
                    participant = page.locator("[data-testid='wcl-dialog-wrapper'] a, div[class*='searchResult'] a").filter(has_text=team_name).first
                    if await participant.is_visible(timeout=2000):
                        self.log(f"Coincidencia exacta (dialog) para '{team_name}'.")
                except Exception:
                    participant = None

            if not participant:
                # Strategy 3: fuzzy match — collect all visible result names
                self.log(f"Sin coincidencia exacta para '{team_name}'. Buscando fuzzy match...")
                result_cells = await page.locator("div[class*='searchResult'] .searchResult__participantName, div[class*='searchResult'] a[class*='participantName']").all()
                candidates = []
                for cell in result_cells:
                    try:
                        txt = (await cell.text_content()).strip()
                        if txt:
                            candidates.append((txt, cell))
                    except Exception:
                        continue
                best_text, best_ratio = _find_best_match([c[0] for c in candidates], team_name)
                if best_text and best_ratio >= 0.45:
                    self.log(f"Fuzzy match: '{best_text}' (similitud: {best_ratio:.0%})")
                    for txt, cell in candidates:
                        if txt == best_text:
                            participant = cell
                            break
                else:
                    # Strategy 4: pick first result if any exist
                    if candidates:
                        self.log(f"Sin buen match. Usando primer resultado: '{candidates[0][0]}'")
                        participant = candidates[0][1]

            if not participant:
                self.log(f"No se encontró el resultado de búsqueda para '{team_name}'.")
                return ""
            await participant.click(timeout=8000)
            await asyncio.sleep(4)
            team_url = page.url.rstrip("/")
            self.log(f"URL base de la selección encontrada: {team_url}")
            return team_url
        except Exception as e:
            self.log(f"Error al hacer clic en el resultado de búsqueda: {str(e)}")
            return ""

    # ── Scrapers específicos ───────────────────────────────────────────────

    async def _scrape_team_stats(self, page) -> dict:
        """Extrae estadísticas generales del partido desde la pestaña Estadísticas."""
        stats = {}
        try:
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            rows = soup.select("div[class*='wcl-row_']")
            for row in rows:
                cat_el = row.select_one("div[class*='wcl-category_']")
                home_el = row.select_one("div[class*='wcl-homeValue_']")
                away_el = row.select_one("div[class*='wcl-awayValue_']")
                if cat_el and home_el and away_el:
                    stats[cat_el.get_text().strip()] = {
                        "home": home_el.get_text().strip(),
                        "away": away_el.get_text().strip()
                    }
            self.log(f"Estadísticas extraídas: {len(stats)} categorías.")
        except Exception as e:
            self.log(f"No se pudieron cargar estadísticas: {str(e)}")
        return stats

    async def _scrape_lineups(self, page, soup=None) -> dict:
        """
        Extrae alineaciones: titulares, suplentes y formación de cada equipo.
        Busca en el HTML actual de la página (debe estar en la pestaña Alineaciones).
        """
        lineups = {"local": {"titulares": [], "suplentes": [], "formacion": ""},
                   "visitante": {"titulares": [], "suplentes": [], "formacion": ""}}

        # ── Selectores de respaldo (usados en toda la función) ──
        MAIN_SELS = [
            "div[class*='tabContent__lineups']",
            "div[class*='lf__lineUp']",
            "div[class*='lineupsContent']",
        ]
        PLAYER_SELS = [
            "*[class*='lineupsParticipantName']",
            "*[class*='participantName']",
            "*[class*='wcl-name']",
            "*[class*='playerName']",
        ]
        # Selector más específico para suplentes (evita capturar elementos con posiciones como "(G)")
        SUBS_PLAYER_SELS = [
            "*[class*='lineupsParticipantName']",
            "*[class*='participantName']",
        ]
        FORM_SELS = [
            "*[class*='formation']",
            "*[class*='wcl-formation']",
        ]
        SUBS_SELS = [
            "div[class*='substitutesList']",
            "div[class*='substitutes']",
            "div[class*='subs']",
        ]

        try:
            if soup is None:
                soup = await self._soup(page)

            # ── DEBUG: buscar clases con palabras clave ──
            html_str = str(soup)
            self.log(f"DEBUG HTML size: {len(html_str)} chars, first 500: {html_str[:500]}")

            # Buscar nombres de clase que contengan palabras clave de lineup
            class_matches = set()
            for cls_match in re.finditer(r'class="([^"]*lineup[^"]*)"', html_str, re.I):
                class_matches.update(cls_match.group(1).split())
            for cls_match in re.finditer(r"class='([^']*lineup[^']*)'", html_str, re.I):
                class_matches.update(cls_match.group(1).split())
            if class_matches:
                self.log(f"DEBUG clases con 'lineup': {sorted(class_matches)[:10]}")
            else:
                # Si no encuentra 'lineup', probar otras palabras
                for kw in ['pitch', 'player', 'subs', 'formation', 'field', 'team']:
                    kw_matches = set()
                    for cls_match in re.finditer(f'class="([^"]*{kw}[^"]*)"', html_str, re.I):
                        kw_matches.update(cls_match.group(1).split())
                    for cls_match in re.finditer(f"class='([^']*{kw}[^']*)'", html_str, re.I):
                        kw_matches.update(cls_match.group(1).split())
                    if kw_matches:
                        self.log(f"DEBUG clases con '{kw}': {sorted(kw_matches)[:8]}")
                        break

            # ── Buscar contenedor principal de lineups ──
            main_container = None
            for sel in MAIN_SELS:
                main_container = soup.select_one(sel)
                if main_container:
                    self.log(f"OK Contenedor principal: {sel}")
                    break

            search_root = main_container if main_container else soup

            # ── Estrategia: agrupar nombres de jugadores por su contenedor padre ──
            # Primero encontrar TODOS los elementos que parecen nombres de jugadores
            all_player_els = []
            for psel in PLAYER_SELS:
                all_player_els = search_root.select(psel)
                if all_player_els:
                    self.log(f"OK Elementos de jugador encontrados: {psel} ({len(all_player_els)} total)")
                    break

            if all_player_els:
                # Agrupar por contenedor padre directo
                from collections import defaultdict
                groups = defaultdict(list)
                for el in all_player_els:
                    parent = el.parent
                    if parent:
                        name = el.get_text().strip()
                        if name:
                            groups[id(parent)].append(name)

                # Quitar duplicados CONSECUTIVOS dentro de cada grupo
                for pid in groups:
                    groups[pid] = list(dict.fromkeys(groups[pid]))

                # Ordenar grupos por cantidad de jugadores (mayor = titulares)
                sorted_groups = sorted(groups.values(), key=len, reverse=True)
                self.log(f"DEBUG grupos: {[len(g) for g in sorted_groups[:6]]}... ({len(sorted_groups)} grupos total)")

                # Tomar los 2 grupos más grandes como titulares
                team_groups = [g for g in sorted_groups if len(g) >= 4][:2]
                if len(team_groups) >= 2:
                    lineups["local"]["titulares"] = team_groups[0]
                    lineups["visitante"]["titulares"] = team_groups[1]
                    self.log(f"OK Titulares por grupos: {len(team_groups[0])} vs {len(team_groups[1])}")

                    # Formación global
                    for fsel in FORM_SELS:
                        form_els = search_root.select(fsel)
                        if form_els:
                            lineups["local"]["formacion"] = form_els[0].get_text().strip()
                            if len(form_els) > 1:
                                lineups["visitante"]["formacion"] = form_els[1].get_text().strip()
                            break
                else:
                    self.log(f"Grupos insuficientes ({len(team_groups)}), split plano...")
                    names = [el.get_text().strip() for el in all_player_els if el.get_text().strip()]
                    if names:
                        half = len(names) // 2
                        lineups["local"]["titulares"] = names[:half]
                        lineups["visitante"]["titulares"] = names[half:]

                # ── SUPLENTES: buscar grupos con 2-9 jugadores (restantes tras titulares) ──
                starter_count = max(len(t) for t in team_groups) if team_groups else 11
                sub_candidates = [g for g in sorted_groups if 2 <= len(g) < starter_count]
                self.log(f"DEBUG candidatos a suplentes: {[len(g) for g in sub_candidates[:4]]} ({len(sub_candidates)} grupos)")
                sub_groups = sub_candidates[:2]

                if len(sub_groups) >= 2:
                    lineups["local"]["suplentes"] = sub_groups[0]
                    lineups["visitante"]["suplentes"] = sub_groups[1]
                    self.log(f"OK Suplentes por grupos: {len(sub_groups[0])} vs {len(sub_groups[1])}")
                elif sub_groups:
                    mid = len(sub_groups[0]) // 2
                    lineups["local"]["suplentes"] = sub_groups[0][:mid]
                    lineups["visitante"]["suplentes"] = sub_groups[0][mid:]
                    self.log(f"OK Suplentes (split único grupo): {mid} vs {len(sub_groups[0]) - mid}")
                else:
                    self.log("Buscando suplentes por separadores de texto...")
                    sub_sections = search_root.find_all(["h4", "span", "div"],
                                                         text=re.compile(r'(suplentes|substitutes|subs|banquillo)', re.I))
                    for idx, sec in enumerate(sub_sections[:2]):
                        side = "local" if idx == 0 else "visitante"
                        parent = sec.parent
                        for psel in SUBS_PLAYER_SELS:
                            names = [el.get_text().strip() for el in parent.select(psel) if el.get_text().strip()]
                            if names:
                                lineups[side]["suplentes"] = list(dict.fromkeys(names))
                                break
                        self.log(f"  Suplentes ({side}): {len(lineups[side]['suplentes'])} encontrados por texto")
            else:
                self.log("No se encontraron nombres de jugadores en la página.")

            n_local_tit = len(lineups["local"]["titulares"])
            n_vis_tit = len(lineups["visitante"]["titulares"])
            n_local_sub = len(lineups["local"]["suplentes"])
            n_vis_sub = len(lineups["visitante"]["suplentes"])
            self.log(f"Alineaciones extraídas: {n_local_tit} vs {n_vis_tit} titulares, {n_local_sub} vs {n_vis_sub} suplentes.")
            if n_local_tit == 0 and n_vis_tit == 0:
                self.log("ADVERTENCIA: No se encontraron titulares. Posible cambio en selectores de Flashscore.")
        except Exception as e:
            self.log(f"No se pudieron cargar alineaciones: {str(e)}")
        return lineups

    async def _scrape_player_stats(self, page) -> dict:
        """
        Extrae estadísticas individuales de jugadores desde la pestaña Jugadores.
        Retorna { "local": [{...}, ...], "visitante": [{...}, ...] }.
        Busca elementos con clase que contenga 'participantName' o 'wcl-name',
        agrupados por tabla contenedora (cada equipo tiene la suya).
        """
        result = {"local": [], "visitante": []}
        try:
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")
            all_text = soup.get_text().lower()

            # Buscar contenedores de tabla de jugadores
            # Flashscore usa clases con hash como wcl-table_XXXXX
            tables = soup.select("div[class*='wcl-table']")

            if not tables:
                # Fallback: buscar secciones que contengan stats numéricas
                tables = soup.select("div[class*='participantsTable'], div[class*='playerTable'], div[class*='tableContainer']")

            for idx, table in enumerate(tables[:2]):
                side = "local" if idx == 0 else "visitante"
                # Buscar filas de jugadores dentro de cada tabla
                rows = table.select("div[class*='wcl-row_']")
                if not rows:
                    # Fallback: buscar cualquier elemento con nombre de jugador
                    player_names = table.select("*[class*='participantName'], *[class*='playerName'], *[class*='wcl-name']")
                    for el in player_names:
                        name = el.get_text().strip()
                        if name:
                            result[side].append({"nombre": name})

                    # Buscar también valores numéricos cercanos (stats)
                    for player_entry in result[side]:
                        parent = None
                        # Encontrar el elemento padre de este nombre
                        for pnm in player_names:
                            if pnm.get_text().strip() == player_entry["nombre"]:
                                parent = pnm.parent
                                break
                        if parent:
                            # Buscar spans con valores numéricos
                            vals = parent.select("span[class*='value'], div[class*='wcl-cell_'], span, div")
                            for i, v in enumerate(vals):
                                txt = v.get_text().strip()
                                if txt and txt != player_entry["nombre"]:
                                    player_entry[f"stat_{i}"] = txt
                else:
                    for row in rows:
                        name_el = row.select_one("*[class*='participantName'], *[class*='playerName'], *[class*='wcl-name']")
                        if not name_el:
                            continue
                        player = {"nombre": name_el.get_text().strip()}
                        cells = row.select("span[class*='value'], div[class*='wcl-cell_'], div[class*='stat-value']")
                        for i, cell in enumerate(cells):
                            val = cell.get_text().strip()
                            if val:
                                player[f"stat_{i}"] = val
                        if player.get("nombre"):
                            result[side].append(player)

            total = len(result["local"]) + len(result["visitante"])
            self.log(f"Estadísticas de jugadores extraídas: {total} jugadores ({len(result['local'])} local, {len(result['visitante'])} visitante).")
        except Exception as e:
            self.log(f"No se pudieron cargar estadísticas de jugadores: {str(e)}")
        return result

    async def _get_match_datetime(self, page) -> datetime:
        """
        Extrae la fecha/hora del partido desde la página del partido.
        Busca múltiples selectores típicos de Flashscore.
        """
        soup = await self._soup(page)
        patterns = [
            "div[class*='duelDetail__datetime']",
            "span[class*='datetime']",
            "div[class*='matchHeader__datetime']",
            "div[class*='detailMS__date']",
            "time[class*='datetime']",
        ]
        for sel in patterns:
            el = soup.select_one(sel)
            if el:
                text = el.get_text().strip()
                # Formatos típicos: "25.06.2026 21:00" o "25.06.2026 21:00" o "2026-06-25 21:00"
                for fmt in ["%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M"]:
                    try:
                        return datetime.strptime(text, fmt)
                    except ValueError:
                        continue
                # Si no matchea formato exacto, intentar extraer fecha con regex
                m = re.search(r'(\d{2})\.(\d{2})\.(\d{4})\s+(\d{2}):(\d{2})', text)
                if m:
                    try:
                        return datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)),
                                        int(m.group(4)), int(m.group(5)))
                    except ValueError:
                        pass
        return None

    async def _scrape_odds(self, page) -> dict:
        """
        Extrae cuotas 1X2 de todas las casas de apuestas disponibles.
        Retorna { "Bet365": {"1":"1.80","X":"3.40","2":"4.50"}, ... }
        """
        odds = {}
        try:
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Buscar tabla de odds o contenedor de cuotas
            # Flashscore usa distintas clases según la versión/idioma
            containers = soup.select(
                "div[class*='odds-table'], div[class*='oddsTable'], "
                "div[class*='market-odds'], div[class*='prematch-odds'], "
                "section[class*='odds'], div[class*='betting'], "
                "div[class*='bookmakerTable'], div[class*='bookmaker-table']"
            )

            if not containers:
                # Fallback: buscar cualquier tabla con odds en toda la página
                containers = [soup]

            for container in containers[:1]:
                rows = container.select(
                    "div[class*='odds-row'], div[class*='oddsRow'], "
                    "div[class*='bookmakerRow'], div[class*='market-row'], "
                    "div[class*='bettingRow']"
                )
                if not rows:
                    # Fallback extremo: buscar filas con 3 números decimales
                    for div in container.find_all("div", recursive=True):
                        text = div.get_text().strip()
                        if re.match(r'^[\d.]+\s+[\d.]+\s+[\d.]+$', text):
                            parent = div.parent
                            name_el = parent.find_previous(["span", "a", "div"],
                                                           text=re.compile(r'[A-Za-z]'))
                            if name_el and len(text.split()) >= 3:
                                vals = text.split()
                                odds[name_el.get_text().strip()] = {
                                    "1": vals[0], "X": vals[1], "2": vals[2]
                                }
                    return odds

                for row in rows:
                    name_el = row.select_one(
                        "span[class*='bookmaker-name'], div[class*='bookmakerName'], "
                        "span[class*='participantName'], a[class*='bookmaker']"
                    )
                    if not name_el:
                        continue
                    bookmaker = name_el.get_text().strip().replace("\n", " ").strip()
                    cells = row.select(
                        "span[class*='odds-value'], span[class*='oddsValue'], "
                        "div[class*='odds-cell'], span[class*='value'], "
                        "span[class*='odds'], div[class*='price']"
                    )
                    values = [c.get_text().strip() for c in cells if c.get_text().strip()]
                    if len(values) >= 3:
                        odds[bookmaker] = {
                            "1": values[0],
                            "X": values[1],
                            "2": values[2]
                        }

            self.log(f"Cuotas extraídas: {len(odds)} casas de apuestas.")
        except Exception as e:
            self.log(f"No se pudieron cargar cuotas: {str(e)}")
        return odds

    # ── Scraper principal ──────────────────────────────────────────────────

    async def scrape_match_data(self, query: str) -> dict:
        team_a = query
        team_b = ""
        for separator in [" vs ", " - ", " contra ", " vs. "]:
            if separator in query:
                parts = query.split(separator)
                team_a = parts[0].strip()
                team_b = parts[1].strip()
                break

        async with async_playwright() as p:
            user_agent = self.get_random_user_agent()
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=user_agent, viewport={"width": 1366, "height": 768}
            )
            page = await context.new_page()

            # 1. Obtener URL base del Equipo A
            team_url = await self.find_team_base_url(page, team_a)
            if not team_url:
                await browser.close()
                return {}

            match_id = ""
            match_type = ""
            match_desc = ""

            def scan_matches(html_content, opponent_name):
                soup = BeautifulSoup(html_content, "html.parser")
                match_divs = soup.find_all("div", id=lambda x: x and x.startswith("g_1_"))
                for div in match_divs:
                    text = div.get_text().lower()
                    if not opponent_name or opponent_name.lower() in text:
                        m_id = div.get("id").replace("g_1_", "")
                        return m_id, div.get_text().strip()
                return "", ""

            # 2. Buscar en Resultados (finalizados)
            results_url = f"{team_url}/resultados/"
            self.log(f"Buscando partido en Resultados: {results_url}")
            await page.goto(results_url, timeout=30000)
            await asyncio.sleep(3)
            html_content = await page.content()
            match_id, match_desc = scan_matches(html_content, team_b)

            if match_id:
                self.log(f"Partido Finalizado encontrado: {match_desc} (ID: {match_id})")
                match_type = "finalizado"
            else:
                # 3. Buscar en Partidos (futuros)
                fixtures_url = f"{team_url}/partidos/"
                self.log(f"Buscando partido en Partidos futuros: {fixtures_url}")
                await page.goto(fixtures_url, timeout=30000)
                await asyncio.sleep(3)
                html_content = await page.content()
                match_id, match_desc = scan_matches(html_content, team_b)

                if match_id:
                    self.log(f"Partido Futuro encontrado: {match_desc} (ID: {match_id})")
                    match_type = "futuro"

            if not match_id:
                opp_str = f" contra '{team_b}'" if team_b else ""
                self.log(f"No se encontró ningún partido reciente o futuro{opp_str} para '{team_a}'.")
                await browser.close()
                return {}

            # 4. Navegar a la página del partido
            from urllib.parse import urlparse
            parsed_team_url = urlparse(team_url)
            base_domain = f"{parsed_team_url.scheme}://{parsed_team_url.netloc}"
            match_page_url = f"{base_domain}/partido/{match_id}/"
            self.log(f"Navegando a página del partido: {match_page_url}")
            await page.goto(match_page_url, timeout=20000)
            await self._cookie_banner(page)

            result = {
                "match_id": match_id,
                "description": match_desc,
                "type": match_type,
                "data": {}
            }

            if match_type == "finalizado":
                # 4a. Estadísticas
                if await self._click_tab(page, ["Estadísticas", "Stats", "Statistics"]):
                    try:
                        await page.wait_for_selector("div[class*='wcl-row_']", timeout=8000)
                    except Exception:
                        self.log("Selector de estadísticas no encontrado, intentando scrapear igual...")
                    result["data"]["estadisticas"] = await self._scrape_team_stats(page)
                else:
                    # Fallback: intentar scrapear sin hacer clic (quizás ya está visible)
                    try:
                        await page.wait_for_selector("div[class*='wcl-row_']", timeout=3000)
                        result["data"]["estadisticas"] = await self._scrape_team_stats(page)
                    except Exception:
                        self.log("No se encontró la pestaña de Estadísticas ni datos visibles.")
                        result["data"]["estadisticas"] = {}

                # 4b. Alineaciones
                if await self._click_tab(page, ["Alineaciones", "Alineación", "Lineups", "Line-up"]):
                    try:
                        await page.wait_for_selector("div[class*='lineup']", timeout=8000)
                    except Exception:
                        self.log("Selector de alineaciones no encontrado, scrapeando igual...")
                    result["data"]["alineaciones"] = await self._scrape_lineups(page)
                    result["data"]["alineaciones"]["confirmado"] = True
                else:
                    result["data"]["alineaciones"] = {}

                # 4c. Estadísticas de jugadores
                if await self._click_tab(page, ["Jugadores", "Players", "Stats por jugador"]):
                    try:
                        await page.wait_for_selector(
                            "div[class*='player-table'], div[class*='participantsTable'], div[class*='participantRow']",
                            timeout=8000
                        )
                    except Exception:
                        self.log("Selector de jugadores no encontrado, scrapeando igual...")
                    result["data"]["jugadores"] = await self._scrape_player_stats(page)
                else:
                    result["data"]["jugadores"] = {}

            elif match_type == "futuro":
                # 4a. Fecha/hora del partido
                match_dt = await self._get_match_datetime(page)
                result["data"]["match_datetime"] = match_dt.isoformat() if match_dt else None

                # Determinar si es probable o confirmado
                is_confirmed = False
                if match_dt:
                    now = datetime.now()
                    diff_hours = (match_dt - now).total_seconds() / 3600
                    is_confirmed = diff_hours < 1
                    self.log(
                        f"Partido en {diff_hours:.1f}h — "
                        f"alineación {'CONFIRMADA' if is_confirmed else 'PROBABLE'}"
                    )

                # 4b. Alineaciones
                if await self._click_tab(page, ["Alineaciones", "Alineación", "Lineups", "Line-up"]):
                    try:
                        await page.wait_for_selector(
                            "div[class*='lineup'], a[class*='lineup__player']",
                            timeout=8000
                        )
                    except Exception:
                        pass
                    # Esperar un poco más si es probable (los datos pueden tardar en cargar)
                    if not is_confirmed:
                        await asyncio.sleep(1)
                    result["data"]["alineaciones"] = await self._scrape_lineups(page)
                    result["data"]["alineaciones"]["confirmado"] = is_confirmed
                else:
                    result["data"]["alineaciones"] = {}

                # 4c. Cuotas
                # Primero intentar con la pestaña Cuotas si existe
                odds_found = False
                if await self._click_tab(page, ["Cuotas", "Odds", "Betting", "Apuestas"]):
                    await asyncio.sleep(2)
                    odds_data = await self._scrape_odds(page)
                    if odds_data:
                        result["data"]["cuotas"] = odds_data
                        odds_found = True

                # Fallback: buscar cuotas directamente en la página principal
                if not odds_found:
                    # Volver a la vista general (pestaña "Resumen" o navegar de nuevo)
                    await page.goto(match_page_url, timeout=15000)
                    await asyncio.sleep(1)
                    odds_data = await self._scrape_odds(page)
                    if odds_data:
                        result["data"]["cuotas"] = odds_data

            await browser.close()
            return result

    # ── Método run (entry point desde main.py) ─────────────────────────────

    def run(self, **kwargs):
        super().run(**kwargs)
        query = kwargs.get("match_id") or kwargs.get("team_name") or "Argentina vs Uruguay"

        self.log("=" * 60)
        self.log(f"  Flashscore Intelligent Scraper — Playwright Module")
        self.log(f"  Búsqueda: {query}")
        self.log("=" * 60)

        if self.sandbox:
            self.log("MODO SANDBOX: Simulando extracción de datos de Flashscore...")
            self.sleep_random(0.1, 0.3)
            
            res = {
                "match_id": "12345",
                "type": "finalizado",
                "description": query,
                "data": {
                    "estadisticas": {
                        "Posesión de balón": {"home": "55%", "away": "45%"},
                        "Remates": {"home": "12", "away": "8"},
                        "Faltas": {"home": "10", "away": "14"}
                    },
                    "alineaciones": {
                        "confirmado": True,
                        "local": {
                            "formacion": "4-3-3",
                            "titulares": ["Emiliano Martínez", "Nahuel Molina", "Cristian Romero", "Nicolás Otamendi", "Nicolás Tagliafico", "Rodrigo De Paul", "Enzo Fernández", "Alexis Mac Allister", "Lionel Messi", "Julián Álvarez", "Ángel Di María"],
                            "suplentes": ["Franco Armani", "Gonzalo Montiel", "Leandro Paredes", "Lautaro Martínez"]
                        },
                        "visitante": {
                            "formacion": "4-4-2",
                            "titulares": ["Sergio Rochet", "Nahitan Nández", "Ronald Araújo", "Sebastián Cáceres", "Mathías Olivera", "Federico Valverde", "Manuel Ugarte", "Nicolás De La Cruz", "Facundo Pellistri", "Darwin Núñez", "Maximiliano Araújo"],
                            "suplentes": ["Santiago Mele", "José María Giménez", "Rodrigo Bentancur", "Luis Suárez"]
                        }
                    },
                    "jugadores": {
                        "local": [
                            {"name": "Lionel Messi", "rating": "8.5", "goals": "1", "assists": "0"},
                            {"name": "Julián Álvarez", "rating": "7.2", "goals": "1", "assists": "0"}
                        ],
                        "visitante": [
                            {"name": "Darwin Núñez", "rating": "7.0", "goals": "1", "assists": "0"},
                            {"name": "Federico Valverde", "rating": "6.8", "goals": "0", "assists": "0"}
                        ]
                    },
                    "cuotas": {
                        "bet365": {"1": "1.80", "X": "3.50", "2": "4.50"},
                        "bwin": {"1": "1.85", "X": "3.40", "2": "4.40"}
                    },
                    "match_datetime": "2026-06-29T20:00:00"
                }
            }
            
            # Guardar JSON
            json_file = self.data_dir / "flashscore_match_data.json"
            existing_data = {}
            if json_file.exists():
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                except Exception:
                    pass
            existing_data[res["match_id"]] = {
                "query": query,
                "description": res["description"],
                "last_updated": self._time_iso(),
                "type": res["type"],
                "data": res["data"]
            }
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            self.log(f"JSON guardado: {json_file}")

            # Guardar CSV
            try:
                self._save_match_csv(res)
            except Exception as e:
                self.log(f"No se pudo guardar CSV: {str(e)}")

            # Set preview data (debe tener match_id, home_team, away_team para la validación de columnas)
            preview_row = {
                "match_id": res["match_id"],
                "home_team": "Argentina",
                "away_team": "Uruguay",
                "home_score": 2,
                "away_score": 1
            }
            self.set_preview_data([preview_row])
            self.log("Simulación de Flashscore finalizada con éxito.")
            return True

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            res = loop.run_until_complete(self.scrape_match_data(query))
        finally:
            if not loop.is_closed():
                loop.close()

        if not res or not res.get("match_id"):
            self.log("Scraping finalizó sin datos.")
            return False

        # ── Guardar JSON ──
        json_file = self.data_dir / "flashscore_match_data.json"
        existing_data = {}
        if json_file.exists():
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except Exception:
                pass
        existing_data[res["match_id"]] = {
            "query": query,
            "description": res["description"],
            "last_updated": self._time_iso(),
            "type": res["type"],
            "data": res["data"]
        }
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        self.log(f"JSON guardado: {json_file}")

        # ── Guardar CSV legible ──
        try:
            self._save_match_csv(res)
        except Exception as e:
            self.log(f"No se pudo guardar CSV: {str(e)}")

        # Resumen de lo que se extrajo
        data = res.get("data", {})
        if data.get("estadisticas"):
            self.log(f"  - Estadísticas del partido: {len(data['estadisticas'])} categorías")
        if data.get("alineaciones"):
            al = data["alineaciones"]
            self.log(f"  - Alineaciones: {len(al.get('local',{}).get('titulares',[]))} vs {len(al.get('visitante',{}).get('titulares',[]))} titulares")
            self.log(f"  - Formación: {al.get('local',{}).get('formacion','?')} vs {al.get('visitante',{}).get('formacion','?')}")
            self.log(f"  - Estado: {'CONFIRMADA' if al.get('confirmado') else 'PROBABLE'}")
        if data.get("jugadores"):
            n_local = len(data["jugadores"].get("local", []))
            n_vis = len(data["jugadores"].get("visitante", []))
            self.log(f"  - Estadísticas de jugadores: {n_local + n_vis} total ({n_local} local, {n_vis} visitante)")
        if data.get("cuotas"):
            self.log(f"  - Cuotas: {len(data['cuotas'])} casas de apuestas")
        if data.get("match_datetime"):
            self.log(f"  - Fecha del partido: {data['match_datetime']}")

        return True

    @staticmethod
    def _time_iso():
        from datetime import datetime
        return datetime.now().isoformat()

    def _save_match_csv(self, result: dict):
        """Guarda los datos del partido en un CSV plano legible."""
        import csv
        mid = result["match_id"]
        csv_dir = self.data_dir / "flashscore_csv"
        csv_dir.mkdir(parents=True, exist_ok=True)
        csv_path = csv_dir / f"match_{mid}.csv"

        rows = []
        # ── Info del partido ──
        rows.append(["# PARTIDO", result.get("description", "")])
        rows.append(["# ID", mid])
        rows.append(["# Tipo", result.get("type", "")])
        rows.append(["# Última actualización", self._time_iso()])
        rows.append([])

        data = result.get("data", {})

        # ── Estadísticas ──
        stats = data.get("estadisticas", {})
        if stats:
            rows.append(["# === ESTADÍSTICAS ==="])
            rows.append(["Categoría", "Local", "Visitante"])
            for cat, vals in stats.items():
                rows.append([cat, vals.get("home", ""), vals.get("away", "")])
            rows.append([])

        # ── Alineaciones ──
        al = data.get("alineaciones", {})
        if al and isinstance(al, dict):
            confirmado = al.get("confirmado", False)
            label = "CONFIRMADA" if confirmado else "PROBABLE"
            rows.append([f"# === ALINEACIONES ({label}) ==="])
            for side in ["local", "visitante"]:
                team_data = al.get(side, {})
                formacion = team_data.get("formacion", "")
                titulares = team_data.get("titulares", [])
                suplentes = team_data.get("suplentes", [])
                rows.append([f"# {side.upper()} (formación: {formacion})"])
                if titulares:
                    rows.append(["# TITULARES"])
                    for p in titulares:
                        rows.append([p])
                if suplentes:
                    rows.append(["# SUPLENTES"])
                    for p in suplentes:
                        rows.append([p])
                rows.append([])

        # ── Estadísticas de jugadores ──
        jug = data.get("jugadores", {})
        if jug:
            rows.append(["# === ESTADÍSTICAS DE JUGADORES ==="])
            for side in ["local", "visitante"]:
                players = jug.get(side, [])
                if not players:
                    continue
                rows.append([f"# {side.upper()}"])
                # Header from first player keys
                if players:
                    header = list(players[0].keys())
                    rows.append(header)
                    for p in players:
                        rows.append([p.get(k, "") for k in header])
                rows.append([])

        # ── Cuotas ──
        odds = data.get("cuotas", {})
        if odds:
            rows.append(["# === CUOTAS ==="])
            rows.append(["Casa", "1", "X", "2"])
            for bookie, vals in odds.items():
                rows.append([bookie, vals.get("1", ""), vals.get("X", ""), vals.get("2", "")])
            rows.append([])

        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        self.log(f"CSV guardado: {csv_path}")
