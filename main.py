import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import json
import subprocess
from datetime import datetime

from predictor import load_data, run_prediction_sim, get_team_history, get_h2h_stats

app = FastAPI(
    title="Predictor Mundial 2026 API",
    description="Backend en FastAPI para simulación de partidos de fútbol y análisis de valor de apuestas.",
    version="2.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Models
class PredictionRequest(BaseModel):
    teamA: str
    teamB: str
    rankA: int
    rankB: int
    fifaWeight: float
    h2hWeight: float
    decayMonths: int
    numSims: int
    oddsA: Optional[float] = None
    oddsDraw: Optional[float] = None
    oddsB: Optional[float] = None
    strengthOverrideA: Optional[float] = 1.0
    strengthOverrideB: Optional[float] = 1.0
    altitude: Optional[int] = 0

@app.get("/api/teams")
def get_teams():
    try:
        _, ratings = load_data()
        return {"ratings": ratings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading ratings: {str(e)}")

@app.post("/api/predict")
def predict_match(req: PredictionRequest):
    try:
        res = run_prediction_sim(
            team_a=req.teamA,
            team_b=req.teamB,
            rank_a=req.rankA,
            rank_b=req.rankB,
            fifa_weight_pct=req.fifaWeight,
            h2h_weight_pct=req.h2hWeight,
            half_life_months=req.decayMonths,
            num_sims=req.numSims,
            odds_a=req.oddsA,
            odds_draw=req.oddsDraw,
            odds_b=req.oddsB,
            strength_override_a=req.strengthOverrideA if req.strengthOverrideA is not None else 1.0,
            strength_override_b=req.strengthOverrideB if req.strengthOverrideB is not None else 1.0,
            altitude=req.altitude if req.altitude is not None else 0
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running simulation: {str(e)}")

@app.get("/api/history/{team_slug}")
def get_history(team_slug: str, decay_months: int = 18):
    try:
        matches, ratings = load_data()
        history = get_team_history(team_slug, matches, ratings, decay_months)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading team history: {str(e)}")

@app.get("/api/h2h/{team_a}/{team_b}")
def get_h2h(team_a: str, team_b: str):
    try:
        matches, _ = load_data()
        h2h = get_h2h_stats(team_a, team_b, matches)
        return h2h
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading H2H stats: {str(e)}")

@app.get("/api/backtest-metrics")
def get_backtest_metrics():
    try:
        backtest_path = os.path.join(BASE_DIR, "data", "model-backtest.json")
        if not os.path.exists(backtest_path):
            return {"status": "none", "message": "No hay backtest generado."}
        with open(backtest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"status": "ok", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading backtest data: {str(e)}")

@app.post("/api/run-backtest")
def run_backtest_command():
    try:
        # Run the node script synchronously
        result = subprocess.run(["node", "backtest.mjs"], cwd=BASE_DIR, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Backtest failed: {result.stderr}")
            
        # Read the newly generated JSON
        backtest_path = os.path.join(BASE_DIR, "data", "model-backtest.json")
        if not os.path.exists(backtest_path):
            raise Exception("Backtest completed but JSON output not found.")
            
        with open(backtest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        return {"status": "success", "data": data, "logs": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

LOGGED_PREDS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "logged_predictions.json")

class LogPredictionRequest(BaseModel):
    teamA: str
    teamB: str
    probWinA: float
    probDraw: float
    probWinB: float
    xgA: float
    xgB: float
    strengthOverrideA: float
    strengthOverrideB: float
    altitude: int

@app.post("/api/log-prediction")
def log_prediction(req: LogPredictionRequest):
    try:
        preds = []
        if os.path.exists(LOGGED_PREDS_PATH):
            try:
                with open(LOGGED_PREDS_PATH, "r", encoding="utf-8") as f:
                    preds = json.load(f)
            except:
                preds = []
                
        new_entry = {
            "id": int(datetime.now().timestamp() * 1000),
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "teamA": req.teamA,
            "teamB": req.teamB,
            "probWinA": req.probWinA,
            "probDraw": req.probDraw,
            "probWinB": req.probWinB,
            "xgA": req.xgA,
            "xgB": req.xgB,
            "strengthOverrideA": req.strengthOverrideA,
            "strengthOverrideB": req.strengthOverrideB,
            "altitude": req.altitude,
            "actualResult": None,
            "status": "pending"
        }
        
        preds.insert(0, new_entry)
        
        with open(LOGGED_PREDS_PATH, "w", encoding="utf-8") as f:
            json.dump(preds, f, indent=2, ensure_ascii=False)
            
        return {"status": "success", "prediction": new_entry}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logged-predictions")
def get_logged_predictions():
    try:
        preds = []
        if os.path.exists(LOGGED_PREDS_PATH):
            with open(LOGGED_PREDS_PATH, "r", encoding="utf-8") as f:
                preds = json.load(f)
        return {"predictions": preds}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ResolvePredictionRequest(BaseModel):
    id: int
    isCorrect: bool

@app.post("/api/resolve-prediction")
def resolve_prediction(req: ResolvePredictionRequest):
    try:
        if not os.path.exists(LOGGED_PREDS_PATH):
            raise HTTPException(status_code=404, detail="No logged predictions found.")
        with open(LOGGED_PREDS_PATH, "r", encoding="utf-8") as f:
            preds = json.load(f)
        
        found = False
        for p in preds:
            if p["id"] == req.id:
                p["status"] = "completed"
                p["isCorrect"] = req.isCorrect
                p["actualResult"] = "Manual"
                p["actualScore"] = "Manual"
                p["rps"] = 0.0 if req.isCorrect else 1.0
                found = True
                break
        
        if not found:
            raise HTTPException(status_code=404, detail="Prediction not found.")
            
        with open(LOGGED_PREDS_PATH, "w", encoding="utf-8") as f:
            json.dump(preds, f, indent=2, ensure_ascii=False)
            
        # Recalculate summary
        completed = [x for x in preds if x["status"] == "completed"]
        correct_count = sum(1 for x in completed if x["isCorrect"])
        total_completed = len(completed)
        accuracy = (correct_count / total_completed * 100.0) if total_completed > 0 else 0.0
        total_rps = sum(x.get("rps", 0.0) for x in completed)
        avg_rps = (total_rps / total_completed) if total_completed > 0 else 0.0
        
        summary = {
            "totalLogged": len(preds),
            "totalCompleted": total_completed,
            "totalPending": len(preds) - total_completed,
            "correctCount": correct_count,
            "accuracyPercent": round(accuracy, 1),
            "avgRps": round(avg_rps, 4)
        }
        
        return {
            "status": "success",
            "predictions": preds,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/update-prediction-results")
def update_prediction_results():
    try:
        if not os.path.exists(LOGGED_PREDS_PATH):
            return {"status": "ok", "message": "No logged predictions to update.", "predictions": [], "summary": {}}
            
        with open(LOGGED_PREDS_PATH, "r", encoding="utf-8") as f:
            preds = json.load(f)
            
        matches, _ = load_data()
        
        completed_lookup = {}
        for m in matches:
            if m.get("hg") is not None and m.get("ag") is not None:
                k = (m["homeSlug"], m["awaySlug"])
                if k not in completed_lookup:
                    completed_lookup[k] = []
                completed_lookup[k].append(m)
                
                k_rev = (m["awaySlug"], m["homeSlug"])
                if k_rev not in completed_lookup:
                    completed_lookup[k_rev] = []
                completed_lookup[k_rev].append(m)
                
        updated_count = 0
        correct_count = 0
        total_completed = 0
        total_rps = 0.0
        
        for p in preds:
            if p["status"] == "pending":
                team_a = p["teamA"]
                team_b = p["teamB"]
                k = (team_a, team_b)
                
                if k in completed_lookup:
                    match_found = None
                    pred_dt_str = p["date"]
                    for m in completed_lookup[k]:
                        if m["date"] >= pred_dt_str:
                            match_found = m
                            break
                    
                    if match_found:
                        hg = match_found["hg"]
                        ag = match_found["ag"]
                        
                        is_a_home = match_found["homeSlug"] == team_a
                        gs_a = hg if is_a_home else ag
                        gs_b = ag if is_a_home else hg
                        
                        if gs_a > gs_b:
                            actual = "A"
                        elif gs_a == gs_b:
                            actual = "Draw"
                        else:
                            actual = "B"
                            
                        p["actualResult"] = actual
                        p["actualScore"] = f"{gs_a}-{gs_b}"
                        p["status"] = "completed"
                        updated_count += 1
                        
            if p["status"] == "completed":
                total_completed += 1
                
                probs = [p["probWinA"], p["probDraw"], p["probWinB"]]
                max_idx = probs.index(max(probs))
                pick = "A" if max_idx == 0 else "Draw" if max_idx == 1 else "B"
                
                p["pick"] = pick
                p["isCorrect"] = pick == p["actualResult"]
                if p["isCorrect"]:
                    correct_count += 1
                    
                actual_val = p["actualResult"]
                y = [1.0 if actual_val == "A" else 0.0, 
                     1.0 if actual_val == "Draw" else 0.0, 
                     1.0 if actual_val == "B" else 0.0]
                probs_vec = [p["probWinA"], p["probDraw"], p["probWinB"]]
                
                # Calculate RPS
                rps_val = 0.5 * ((probs_vec[0] - y[0])**2 + (probs_vec[0] + probs_vec[1] - y[0] - y[1])**2)
                p["rps"] = round(rps_val, 4)
                total_rps += rps_val
                
        if updated_count > 0:
            with open(LOGGED_PREDS_PATH, "w", encoding="utf-8") as f:
                json.dump(preds, f, indent=2, ensure_ascii=False)
                
        accuracy = (correct_count / total_completed * 100.0) if total_completed > 0 else 0.0
        avg_rps = (total_rps / total_completed) if total_completed > 0 else 0.0
        
        summary = {
            "totalLogged": len(preds),
            "totalCompleted": total_completed,
            "totalPending": len(preds) - total_completed,
            "correctCount": correct_count,
            "accuracyPercent": round(accuracy, 1),
            "avgRps": round(avg_rps, 4)
        }
        
        return {
            "status": "success",
            "message": f"Updated {updated_count} prediction results.",
            "predictions": preds,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files (HTML, CSS, JS) at the end, so it doesn't mask API routes
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
