import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os

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
            odds_b=req.oddsB
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

# Mount static files (HTML, CSS, JS) at the end, so it doesn't mask API routes
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
