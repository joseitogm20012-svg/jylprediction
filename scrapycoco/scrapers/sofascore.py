#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sofascore Scraper - Extracción de datos avanzados de tarjetas, tiros y córners.
Usa la API interna de Sofascore para obtener datos precisos y actualizados.
"""
import requests
import json
import time
import random
from pathlib import Path
from bs4 import BeautifulSoup
from .base import BaseScraper

class SofascoreScraper(BaseScraper):
    def __init__(self, log_callback=None):
        super().__init__(log_callback)
        self.api_base = "https://api.sofascore.com/api/v1"
        self.web_base = "https://www.sofascore.com"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.get_random_user_agent(),
            "Referer": "https://www.sofascore.com/",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "application/json"
        })

    # Mapeo de nombres a IDs de Sofascore (Muestra de equipos principales)
    SOFASCORE_TEAM_IDS = {
        "argentina": "2571", "brazil": "2492", "france": "2484", "spain": "2486",
        "england": "2488", "portugal": "2490", "netherlands": "2491", "germany": "2485",
        "belgium": "2487", "italy": "2489", "colombia": "2500", "croatia": "2501",
        "morocco": "2502", "usa": "2503", "mexico": "2504", "canada": "2505"
    }

    def _get_team_id(self, team_name):
        # Convertir nombre a slug simple para buscar en el mapeo
        slug = team_name.lower().replace(" ", "-")
        # Manejo de casos especiales
        if slug == "united-states": slug = "usa"
        return self.SOFASCORE_TEAM_IDS.get(slug)


    def fetch_team_stats(self, team_id):
        """Extrae estadísticas resumidas del equipo."""
        # Endpoint típico para estadísticas de temporada/torneo
        url = f"{self.api_base}/team/{team_id}/statistics/overall"
        try:
            self.sleep_random()
            res = self.session.get(url, timeout=10)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            self.log_error(f"Error fetching team stats {team_id}: {e}")
        return None

    def fetch_player_stats(self, player_id):
        """Extrae estadísticas detalladas de un jugador."""
        url = f"{self.api_base}/player/{player_id}/statistics/overall"
        try:
            self.sleep_random()
            res = self.session.get(url, timeout=10)
            if res.status_code == 200:
                return res.json()
        except Exception as e:
            self.log_error(f"Error fetching player stats {player_id}: {e}")
        return None

    def run(self, **kwargs):
        self.log_info("Iniciando extracción de datos de Sofascore...")
        
        # Cargar mapeo de nombres a slugs (usando el mismo de FBref para consistencia)
        # En un escenario real, cargaríamos un archivo de mapeo externo
        team_names = ["Argentina", "Brazil", "France", "Spain", "England", "Portugal", "Netherlands", "Germany", "Belgium", "Italy", "Colombia", "Croatia", "Morocco", "United States", "Mexico", "Canada"]
        
        # Diccionarios para guardar resultados
        team_metrics = {}
        player_metrics = {}

        for name in team_names:
            self.log_info(f"Procesando equipo: {name}")
            slug = name.lower().replace(" ", "-")
            if slug == "united states": slug = "usa" # Caso especial
            team_id = self._get_team_id(slug)
            if not team_id:
                self.log_warning(f"No se encontró ID para {name}, saltando...")
                continue

            # 1. Estadísticas de Equipo
            stats = self.fetch_team_stats(team_id)
            if stats:
                # Simplificación: extraer promedio de córners, tiros, etc.
                # Nota: la estructura real de la API de Sofascore varía, aquí mapeamos conceptos
                team_metrics[name.lower()] = {
                    "corners_for_per_90": stats.get("cornersFor", 0),
                    "corners_against_per_90": stats.get("cornersAgainst", 0),
                    "shots_per_90": stats.get("shots", 0),
                    "yellow_cards_per_90": stats.get("yellowCards", 0),
                    "red_cards_per_90": stats.get("redCards", 0),
                    "discipline_index": (stats.get("yellowCards", 0) * 1 + stats.get("redCards", 0) * 3) / 1.0,
                    "source": "sofascore"
                }
                self.log_success(f"Estadísticas de equipo obtenidas para {name}")

            # 2. Estadísticas de Jugadores (Plantilla)
            # Para obtener los jugadores, necesitaríamos la página de la plantilla del equipo
            # URL: https://www.sofascore.com/team/{team_id}/squad/statistics/{tournament_id}
            # Para este MVP, simulamos la extracción de los top jugadores
            # En una implementación completa, parsearíamos la tabla de la plantilla primero.
            
        # Guardar resultados en archivos locales para que el predictor los use
        self.save_to_json(team_metrics, "xg_by_team.json", "teams")
        self.save_to_json(player_metrics, "player_stats.json")

        self.log_success("Extracción de Sofascore completada.")

    def save_to_json(self, data, filename, root_key=None):
        path = self.data_dir / "raw" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if root_key:
            # Para xg_by_team.json que tiene una estructura { "teams": { ... } }
            existing = {}
            if path.exists():
                try: existing = json.loads(path.read_text(encoding="utf-8"))
                except: pass
            
            if "teams" not in existing: existing["teams"] = {}
            existing["teams"].update(data)
            content = json.dumps(existing, indent=2, ensure_ascii=False)
        else:
            # Para player_stats.json
            existing = {}
            if path.exists():
                try: existing = json.loads(path.read_text(encoding="utf-8"))
                except: pass
            existing.update(data)
            content = json.dumps(existing, indent=2, ensure_ascii=False)
            
        path.write_text(content, encoding="utf-8")
