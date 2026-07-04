import pytest
from httpx import AsyncClient, ASGITransport
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert "scrapers_count" in data
    assert "spiders_available" in data


@pytest.mark.asyncio
async def test_list_scrapers(client):
    r = await client.get("/api/scrapers")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 13
    for s in data:
        assert "id" in s
        assert "name" in s
        assert "status" in s


@pytest.mark.asyncio
async def test_scrapy_spiders(client):
    r = await client.get("/api/scrapy/spiders")
    assert r.status_code == 200
    data = r.json()
    assert "spiders" in data
    assert "fbref" in data["spiders"]
    assert "flashscore" in data["spiders"]


@pytest.mark.asyncio
async def test_history_empty(client):
    r = await client.get("/api/history")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_history_metrics(client):
    r = await client.get("/api/history/metrics")
    assert r.status_code == 200
    data = r.json()
    assert "total_runs" in data


@pytest.mark.asyncio
async def test_history_stats(client):
    r = await client.get("/api/history/stats")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_quality_overview(client):
    r = await client.get("/api/quality")
    assert r.status_code == 200
    data = r.json()
    assert "overall_quality_score" in data
    assert data["overall_quality_score"] == 100.0


@pytest.mark.asyncio
async def test_rate_limit(client):
    r = await client.get("/api/rate-limit")
    assert r.status_code == 200
    data = r.json()
    assert "remaining" in data
    assert data["limit"] == 60


@pytest.mark.asyncio
async def test_export_filtered(client):
    r = await client.get("/api/export/filtered?format=json&limit=5")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_scheduler_list(client):
    r = await client.get("/api/scheduler/list")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_swagger_docs(client):
    r = await client.get("/docs")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_openapi_schema(client):
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    schema = r.json()
    assert schema["info"]["title"] == "ScrapyCoco API - Suite de Scraping Modular"
    assert schema["info"]["version"] == "2.0.0"
    paths = schema["paths"]
    assert "/api/health" in paths
    assert "/api/scrapers" in paths
    assert "/api/scrapy/spiders" in paths
    assert "/api/quality" in paths
    assert "/api/history" in paths
    assert "/api/pipeline/run" in paths
    assert len(paths) >= 15


@pytest.mark.asyncio
async def test_pipeline_run(client):
    r = await client.post("/api/pipeline/run", json={
        "item_type": "match",
        "items": [
            {
                "home_team": "Barcelona",
                "away_team": "Real Madrid",
                "home_goals": 2,
                "away_goals": 1,
                "match_date": "2026-07-01",
                "competition": "La Liga",
                "season": "2026-2027",
                "status": "completed",
            }
        ],
        "scraper_id": "test",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["result"]["success"] is True
    assert data["items_out"] == 1


@pytest.mark.asyncio
async def test_pipeline_dedup(client):
    r = await client.post("/api/pipeline/run", json={
        "item_type": "match",
        "items": [
            {"home_team": "A", "away_team": "B", "match_date": "2026-07-01",
             "competition": "Test", "season": "2026-2027", "status": "completed"},
            {"home_team": "A", "away_team": "B", "match_date": "2026-07-01",
             "competition": "Test", "season": "2026-2027", "status": "completed"},
        ],
        "scraper_id": "test_dedup",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["result"]["duplicates_removed"] >= 1


@pytest.mark.asyncio
async def test_invalid_scraper(client):
    r = await client.get("/api/run/nonexistent")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_index_html(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")


@pytest.mark.asyncio
async def test_batch_run_validation(client):
    r = await client.post("/api/batch/run", json={"scraper_ids": ["nonexistent"]})
    assert r.status_code == 404
