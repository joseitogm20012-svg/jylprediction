import os
import sqlite3
import pytest
from fastapi.testclient import TestClient
from main import app, get_current_user_from_supabase
import db

# 1. Override Supabase Auth dependency for testing
def mock_get_current_user(authorization=None):
    return {
        "id": "test-user-id-999",
        "email": "tester@domain.com",
        "user_metadata": {
            "username": "TestGamer",
            "display_name": "TestGamer"
        }
    }

import main
main.get_current_user_from_supabase = mock_get_current_user
app.dependency_overrides[main.get_current_user_from_supabase] = mock_get_current_user

client = TestClient(app)

def test_sqlite_db_directly():
    print("\n--- TEST: SQLite DB Direct Functions ---")
    db.init_db()
    
    # Clean up test user's data
    user_id = "test-user-id-999"
    conn = db.get_db_connection()
    conn.execute("DELETE FROM favorites WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM user_presets WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM match_votes WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM user_pronostics WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM leaderboard WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    
    # Test Favorites
    fav_id = db.add_favorite(user_id, "argentina", "brazil", 1.8, 1.2, 0.45, 0.25, 0.30, "Notes test")
    assert fav_id is not None
    
    favs = db.get_user_favorites(user_id)
    assert len(favs) == 1
    assert favs[0]["team_a"] == "argentina"
    assert favs[0]["notes"] == "Notes test"
    
    # Test Presets
    preset_id = db.add_user_preset(user_id, "My Preset", 20.0, 30.0, 12, 1.1, 0.9, 2500)
    assert preset_id is not None
    
    presets = db.get_user_presets(user_id)
    assert len(presets) == 1
    assert presets[0]["preset_name"] == "My Preset"
    
    # Test Votes
    match_key = db.get_match_key("argentina", "brazil")
    ok = db.cast_vote(match_key, user_id, "A")
    assert ok is True
    
    stats = db.get_match_votes_stats(match_key)
    assert stats["total"] == 1
    assert stats["percentages"]["A"] == 100
    
    # Test Pronostics and Leaderboard resolution
    ok = db.register_official_pronostic(user_id, "TestGamer", "argentina", "brazil", "A")
    assert ok is True
    
    # Double submission should fail
    ok = db.register_official_pronostic(user_id, "TestGamer", "argentina", "brazil", "B")
    assert ok is False
    
    # Resolve match
    db.resolve_user_pronostics("argentina", "brazil", "A")
    
    # Check pronostic is completed
    pron = db.get_user_match_pronostic(user_id, "argentina", "brazil")
    assert pron["status"] == "completed"
    assert pron["is_correct"] == 1
    
    # Check leaderboard points
    rankings = db.get_leaderboard_rankings()
    assert len(rankings) == 1
    assert rankings[0]["username"] == "TestGamer"
    assert rankings[0]["points"] == 10
    
    print("[OK] Direct SQLite DB tests passed successfully.")

def test_api_routes_via_client():
    print("\n--- TEST: FastAPI API Endpoints ---")
    headers = {"Authorization": "Bearer mock-token"}
    
    # 1. Test Favorites API
    fav_payload = {
        "teamA": "uruguay",
        "teamB": "canada",
        "xgA": 1.5,
        "xgB": 1.1,
        "probWinA": 0.45,
        "probDraw": 0.25,
        "probWinB": 0.30,
        "notes": "Test note from API"
    }
    res = client.post("/api/user/favorites", json=fav_payload, headers=headers)
    assert res.status_code == 200
    fav_id = res.json()["favorite_id"]
    
    res = client.get("/api/user/favorites", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["favorites"]) > 0
    
    # Delete favorite
    res = client.delete(f"/api/user/favorites/{fav_id}", headers=headers)
    assert res.status_code == 200
    
    # 2. Test Presets API
    preset_payload = {
        "presetName": "Offensive Model",
        "fifaWeight": 15.0,
        "h2hWeight": 45.0,
        "decayMonths": 24.0,
        "strengthOverrideA": 1.05,
        "strengthOverrideB": 0.95,
        "altitude": 0
    }
    res = client.post("/api/user/presets", json=preset_payload, headers=headers)
    assert res.status_code == 200
    preset_id = res.json()["preset_id"]
    
    res = client.get("/api/user/presets", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["presets"]) > 0
    
    res = client.delete(f"/api/user/presets/{preset_id}", headers=headers)
    assert res.status_code == 200
    
    # 3. Test Poll Votes API
    vote_payload = {
        "teamA": "france",
        "teamB": "spain",
        "vote": "Draw"
    }
    res = client.post("/api/match/vote", json=vote_payload, headers=headers)
    assert res.status_code == 200
    
    res = client.get("/api/match/vote/france/spain", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["user_vote"] == "Draw"
    assert data["stats"]["total"] == 1
    
    # 4. Test Official Pronostic & Leaderboard API
    prono_payload = {
        "teamA": "germany",
        "teamB": "italy",
        "guess": "B"
    }
    res = client.post("/api/match/pronostic", json=prono_payload, headers=headers)
    assert res.status_code == 200
    
    res = client.get("/api/match/pronostic/germany/italy", headers=headers)
    assert res.status_code == 200
    assert res.json()["pronostic"]["guess"] == "B"
    assert res.json()["pronostic"]["status"] == "pending"
    
    # Retrieve Leaderboard
    res = client.get("/api/leaderboard")
    assert res.status_code == 200
    assert "leaderboard" in res.json()
    
    print("[OK] FastAPI endpoints tests passed successfully.")

if __name__ == "__main__":
    test_sqlite_db_directly()
    test_api_routes_via_client()
    print("\n==================================================")
    print("[EXITO] TODOS LOS TESTS DE CARACTERISTICAS PASARON")
    print("==================================================")
