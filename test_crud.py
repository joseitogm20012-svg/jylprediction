import os
import json
from fastapi.testclient import TestClient
from main import app, AI_ANALYSES_PATH

client = TestClient(app)

def test_ai_crud_flow():
    # Make sure we use a clean test DB file path
    test_db_path = AI_ANALYSES_PATH
    if os.path.exists(test_db_path):
        # Backup original
        try:
            with open(test_db_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)
        except:
            backup_data = []
    else:
        backup_data = []

    try:
        # Clear database for testing
        with open(test_db_path, "w", encoding="utf-8") as f:
            json.dump([], f)
            
        # 1. Test verify auth (success & failure)
        res = client.post("/api/ai-auth/verify", json={"password": "wrongpassword"})
        assert res.status_code == 401
        
        res = client.post("/api/ai-auth/verify", json={"password": "torete69"})
        assert res.status_code == 200
        assert res.json()["status"] == "success"
        
        # 2. Test create analysis without password (should fail)
        payload = {
            "teamA": "argentina",
            "teamB": "venezuela",
            "analysisText": "Test analysis narrative",
            "keyTips": ["Pick 1", "Pick 2"],
            "confidence": 85,
            "predictedScore": "2-0",
            "modelName": "Claude 3.5",
            "stage": "Fase de Grupos",
            "keyPlayers": "Messi (Ok)"
        }
        res = client.post("/api/ai-analyses", json=payload)
        assert res.status_code == 401
        
        # 3. Test create analysis with wrong password (should fail)
        res = client.post("/api/ai-analyses", json=payload, headers={"X-Admin-Password": "wrongpassword"})
        assert res.status_code == 401
        
        # 4. Test create analysis with correct password (should succeed)
        res = client.post("/api/ai-analyses", json=payload, headers={"X-Admin-Password": "torete69"})
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "success"
        analysis_id = data["analysis"]["id"]
        assert data["analysis"]["match_key"] == "argentina-venezuela"
        
        # 5. Test retrieve analyses
        res = client.get("/api/ai-analyses")
        assert res.status_code == 200
        assert len(res.json()["analyses"]) == 1
        
        # 6. Test retrieve specific match (argentina vs venezuela)
        res = client.get("/api/ai-analyses/argentina/venezuela")
        assert res.status_code == 200
        assert res.json()["status"] == "success"
        assert res.json()["analysis"]["analysis_text"] == "Test analysis narrative"
        
        # 7. Test retrieve specific match with reversed order (venezuela vs argentina)
        res = client.get("/api/ai-analyses/venezuela/argentina")
        assert res.status_code == 200
        assert res.json()["status"] == "success"
        assert res.json()["analysis"]["analysis_text"] == "Test analysis narrative"
        
        # 8. Test edit analysis (updating text and confidence)
        payload["id"] = analysis_id
        payload["analysisText"] = "Updated narrative text"
        payload["confidence"] = 90
        res = client.post("/api/ai-analyses", json=payload, headers={"X-Admin-Password": "torete69"})
        assert res.status_code == 200
        
        # Verify update
        res = client.get("/api/ai-analyses/argentina/venezuela")
        assert res.json()["analysis"]["analysis_text"] == "Updated narrative text"
        assert res.json()["analysis"]["confidence"] == 90
        
        # 9. Test delete without auth (should fail)
        res = client.delete(f"/api/ai-analyses/{analysis_id}")
        assert res.status_code == 401
        
        # 10. Test delete with correct auth (should succeed)
        res = client.delete(f"/api/ai-analyses/{analysis_id}", headers={"X-Admin-Password": "torete69"})
        assert res.status_code == 200
        assert res.json()["status"] == "success"
        
        # Verify deleted
        res = client.get("/api/ai-analyses/argentina/venezuela")
        assert res.json()["status"] == "not_found"
        
        print("\n==================================================")
        print("[EXITO] TODOS LOS TESTS DEL CRUD DE IA PASARON OK")
        print("==================================================")

    finally:
        # Restore backup
        with open(test_db_path, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    test_ai_crud_flow()
