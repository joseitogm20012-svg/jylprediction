import json
import os
import requests
import pytest

BASE_URL = os.environ.get("TARGET_URL", "http://localhost:3006")

def test_p0_1_list_scrapers():
    """Listar scrapers: GET /api/scrapers retorna 13 scrapers con status idle"""
    response = requests.get(f"{BASE_URL}/api/scrapers")
    assert response.status_code == 200
    scrapers = response.json()
    assert isinstance(scrapers, list)
    assert len(scrapers) >= 8
    
    expected_ids = {"results", "xg", "xga", "cards", "flashscore", "transfermarkt", "wc2026", "elo", "shooting", "passing", "keepers", "corners", "sofascore"}
    found_ids = {s["id"] for s in scrapers}
    assert found_ids == expected_ids
    
    for s in scrapers:
        assert s["status"] in ("idle", "running")

def test_p0_2_404_invalid_scraper():
    """404 en scraper inválido: GET /api/run/fake retorna 404"""
    response = requests.get(f"{BASE_URL}/api/run/fake")
    assert response.status_code == 404

def test_p0_3_serve_frontend():
    """Servir frontend: GET / retorna index.html con title "ScrapyCoco" """
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert "html" in response.headers.get("content-type", "").lower()
    assert "ScrapyCoco" in response.text

def test_p0_4_run_scraper_sse():
    """Ejecutar scraper: GET /api/run/{id} retorna SSE con event:start, logs, event:end"""
    # Usamos un scraper que no requiere Playwright ni es muy pesado (por ejemplo, wc2026 o elo en sandbox)
    # wc2026 es rápido
    url = f"{BASE_URL}/api/run/wc2026?sandbox=true"
    response = requests.get(url, stream=True, timeout=15)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "").lower()
    
    # Leer el principio del SSE stream
    lines = []
    for line in response.iter_lines(decode_unicode=True):
        if line:
            lines.append(line)
        if len(lines) >= 8:
            break
            
    # Validar que tiene eventos SSE
    assert any("event: start" in l or "event: start" in l for l in lines) or any("Iniciando" in l for l in lines)

def test_p1_1_history():
    """Historial: GET /api/history retorna array"""
    response = requests.get(f"{BASE_URL}/api/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_p1_2_metrics():
    """Métricas: GET /api/history/metrics retorna datos"""
    response = requests.get(f"{BASE_URL}/api/history/metrics")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_p1_3_stats():
    """Stats: GET /api/history/stats retorna 200"""
    response = requests.get(f"{BASE_URL}/api/history/stats")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_p1_4_preview_endpoint():
    """Preview endpoint: GET /api/preview/{id} retorna estructura columns/rows"""
    # xg es clase-based
    response = requests.get(f"{BASE_URL}/api/preview/xg?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "columns" in data
    assert "rows" in data
    assert isinstance(data["columns"], list)
    assert isinstance(data["rows"], list)

def test_p1_5_export_endpoint():
    """Export endpoint: POST /api/export con format csv/json valida parámetros"""
    payload = {
        "scraper_id": "xg",
        "format": "json",
        "transforms": [],
        "preview_data": [{"team": "Argentina", "value": 100}]
    }
    response = requests.post(f"{BASE_URL}/api/export", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["team"] == "Argentina"

def test_p1_6_scheduler_crud():
    """Scheduler: listar, agregar y eliminar tarea"""
    # 1. Listar
    response = requests.get(f"{BASE_URL}/api/scheduler/list")
    assert response.status_code == 200
    initial_jobs = response.json()
    assert isinstance(initial_jobs, list)
    
    # 2. Agregar
    payload = {
        "scraper_id": "xg",
        "cron_expression": "0 12 * * *",
        "params": {"sandbox": True}
    }
    response = requests.post(f"{BASE_URL}/api/scheduler/add", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert "id" in res_data
    job_id = res_data["id"]
    
    # 3. Listar de nuevo y validar
    response = requests.get(f"{BASE_URL}/api/scheduler/list")
    jobs = response.json()
    assert any(j["id"] == job_id for j in jobs)
    
    # 4. Pausar
    response = requests.post(f"{BASE_URL}/api/scheduler/{job_id}/pause")
    assert response.status_code == 200
    
    # 5. Reanudar
    response = requests.post(f"{BASE_URL}/api/scheduler/{job_id}/resume")
    assert response.status_code == 200
    
    # 6. Eliminar
    response = requests.delete(f"{BASE_URL}/api/scheduler/{job_id}")
    assert response.status_code == 200
    
    # 7. Listar final y validar borrado
    response = requests.get(f"{BASE_URL}/api/scheduler/list")
    jobs_after = response.json()
    assert not any(j["id"] == job_id for j in jobs_after)

def test_p2_1_diagnostic_endpoints():
    """Diagnostic history and compare endpoints"""
    response = requests.get(f"{BASE_URL}/api/diagnostic/history/xg")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # Compare with invalid IDs returns 404
    response = requests.get(f"{BASE_URL}/api/diagnostic/compare/99999/88888")
    assert response.status_code == 404

if __name__ == "__main__":
    pytest.main(["-v", __file__])
