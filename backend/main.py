import uvicorn
from fastapi import FastAPI, HTTPException, Header, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import os
import json
import subprocess
import sys
from datetime import datetime
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Asegurar que backend/ esté en sys.path para imports relativos
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Cargar variables de entorno desde el archivo .env en la raíz
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

from predictor import load_data, run_prediction_sim, get_team_history, get_h2h_stats, compute_advanced_h2h, run_betbuilder_sim
import db
from routes.equipo_routes import router as equipo_router

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
TM_STATS_PATH = os.path.join(PROJECT_ROOT, "data", "transfermarkt_stats.json")

_cached_tm_stats = None

def _load_tm_stats():
    global _cached_tm_stats
    if _cached_tm_stats is None and os.path.exists(TM_STATS_PATH):
        try:
            with open(TM_STATS_PATH, "r", encoding="utf-8") as f:
                _cached_tm_stats = json.load(f)
        except Exception:
            _cached_tm_stats = {}
    return _cached_tm_stats or {}

# Configuración desde variables de entorno (ver .env.example)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_PUBLISHABLE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY", "")

app = FastAPI(
    title="Predictor Mundial 2026 API",
    description="Backend en FastAPI para simulación de partidos de fútbol y análisis de valor de apuestas.",
    version="2.0.0"
)

# Security: Rate Limiting
# Security: Rate Limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute", "50/second"])
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")

# Security: CORS - Restrict to configured origins
cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Admin-Password"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

# Security: Add security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    # CSP for API responses
    if request.url.path.startswith("/api/"):
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    return response

# API Models with strict validation
TEAM_SLUG_REGEX = r"^[a-z][a-z0-9-]{1,50}$"
ALLOWED_HOSTS_REGEX = r"^[a-z]$"

class PredictionRequest(BaseModel):
    teamA: str = Field(pattern=TEAM_SLUG_REGEX, max_length=50)
    teamB: str = Field(pattern=TEAM_SLUG_REGEX, max_length=50)
    rankA: int = Field(ge=1, le=211)
    rankB: int = Field(ge=1, le=211)
    fifaWeight: float = Field(ge=0.0, le=100.0)
    h2hWeight: float = Field(ge=0.0, le=100.0)
    decayMonths: int = Field(ge=1, le=120)
    numSims: int = Field(ge=100, le=200000)
    oddsA: Optional[float] = Field(default=None, ge=1.01, le=100.0)
    oddsDraw: Optional[float] = Field(default=None, ge=1.01, le=100.0)
    oddsB: Optional[float] = Field(default=None, ge=1.01, le=100.0)
    strengthOverrideA: Optional[float] = Field(default=1.0, ge=0.1, le=3.0)
    strengthOverrideB: Optional[float] = Field(default=1.0, ge=0.1, le=3.0)
    altitude: Optional[int] = Field(default=0, ge=0, le=5000)
    hostCountry: Optional[str] = Field(default=None, max_length=20)
    refereeIntensity: Optional[float] = Field(default=1.0, ge=0.5, le=2.0)
    predictHalf: Optional[str] = Field(default="full", pattern="^(full|first-half|second-half)$")

    @field_validator("teamA", "teamB")
    @classmethod
    def lower_teams(cls, v: str) -> str:
        return v.strip().lower()

    @field_validator("hostCountry")
    @classmethod
    def validate_host(cls, v: str | None) -> str | None:
        if v:
            cleaned = v.strip().lower()
            if cleaned not in ["", "usa", "mexico", "canada"]:
                raise ValueError("hostCountry must be one of: usa, mexico, canada")
            return cleaned
        return v

class BetBuilderRequest(BaseModel):
    teamA: str = Field(pattern=TEAM_SLUG_REGEX, max_length=50)
    teamB: str = Field(pattern=TEAM_SLUG_REGEX, max_length=50)
    rankA: int = Field(ge=1, le=211)
    rankB: int = Field(ge=1, le=211)
    fifaWeight: float = Field(ge=0.0, le=100.0)
    h2hWeight: float = Field(ge=0.0, le=100.0)
    decayMonths: int = Field(ge=1, le=120)
    numSims: int = Field(default=100000, ge=100, le=200000)
    strengthOverrideA: Optional[float] = Field(default=1.0, ge=0.1, le=3.0)
    strengthOverrideB: Optional[float] = Field(default=1.0, ge=0.1, le=3.0)
    altitude: Optional[int] = Field(default=0, ge=0, le=5000)
    hostCountry: Optional[str] = Field(default=None, max_length=20)
    legs: List[str] = Field(default_factory=list, max_length=20)

    @field_validator("teamA", "teamB")
    @classmethod
    def lower_teams(cls, v: str) -> str:
        return v.strip().lower()

@app.get("/api/config")
@limiter.limit("30/minute")
def get_public_config(request: Request):
    """Expone solo claves públicas de Supabase al frontend (anon key)."""
    if not SUPABASE_URL or not SUPABASE_PUBLISHABLE_KEY:
        raise HTTPException(
            status_code=503,
            detail="Supabase no configurado. Define SUPABASE_URL y SUPABASE_PUBLISHABLE_KEY."
        )
    return {
        "supabaseUrl": SUPABASE_URL,
        "supabaseAnonKey": SUPABASE_PUBLISHABLE_KEY,
    }

@app.get("/api/corners-stats")
def get_corners_stats():
    """Devuelve las estadísticas base de corners (FootyStats + Footiqo)."""
    try:
        from predictor import load_corners_data
        stats = load_corners_data()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading corner stats: {str(e)}")

@app.get("/api/teams")
def get_teams():
    try:
        _, ratings = load_data()
        tm_stats = _load_tm_stats()
        return {"ratings": ratings, "transfermarkt": tm_stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading ratings: {str(e)}")

@app.post("/api/predict")
@limiter.limit("30/minute")
def predict_match(request: Request, req: PredictionRequest):
    try:
        from predictor import load_corners_data
        
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
            altitude=req.altitude if req.altitude is not None else 0,
            host_country=req.hostCountry,
            referee_intensity=req.refereeIntensity if req.refereeIntensity is not None else 1.0,
            predict_half=req.predictHalf
        )
        
        # Add base stats to the response for the frontend to show
        corners_data = load_corners_data()
        stats_a = corners_data.get(req.teamA.lower(), {})
        stats_b = corners_data.get(req.teamB.lower(), {})
        
        res["base_stats"] = {
            "teamA": stats_a,
            "teamB": stats_b
        }
        
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running simulation: {str(e)}")

@app.post("/api/betbuilder/simulate")
@limiter.limit("15/minute")
def betbuilder_simulate(request: Request, req: BetBuilderRequest):
    try:
        res = run_betbuilder_sim(
            team_a=req.teamA,
            team_b=req.teamB,
            rank_a=req.rankA,
            rank_b=req.rankB,
            fifa_weight_pct=req.fifaWeight,
            h2h_weight_pct=req.h2hWeight,
            half_life_months=req.decayMonths,
            num_sims=req.numSims,
            legs=req.legs,
            strength_override_a=req.strengthOverrideA if req.strengthOverrideA is not None else 1.0,
            strength_override_b=req.strengthOverrideB if req.strengthOverrideB is not None else 1.0,
            altitude=req.altitude if req.altitude is not None else 0,
            host_country=req.hostCountry
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in bet builder simulation: {str(e)}")

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

@app.get("/api/history/advanced/{team_a}/{team_b}")
def get_history_advanced(team_a: str, team_b: str):
    try:
        matches, ratings = load_data()
        result = compute_advanced_h2h(team_a, team_b, matches, ratings)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading advanced H2H: {str(e)}")

@app.get("/api/scorers/{team_slug}")
def get_team_scorers_api(team_slug: str, decay_months: Optional[int] = None):
    try:
        from predictor import get_scorers_for_team
        data = get_scorers_for_team(team_slug, decay_months)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading scorers: {str(e)}")


@app.get("/api/backtest-metrics")
def get_backtest_metrics():
    try:
        backtest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "model-backtest.json")
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
        result = subprocess.run(["node", "backtest.mjs"], cwd=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backtesting"), capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Backtest failed: {result.stderr}")
        
        # Read the newly generated JSON
        backtest_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "model-backtest.json")

        if not os.path.exists(backtest_path):
            raise Exception("Backtest completed but JSON output not found.")
            
        with open(backtest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        return {"status": "success", "data": data, "logs": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

LOGGED_PREDS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "logged_predictions.json")

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
    actualResult: Optional[str] = None

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
                
                # Determine actual outcome
                probs = [p["probWinA"], p["probDraw"], p["probWinB"]]
                max_idx = probs.index(max(probs))
                pick = "A" if max_idx == 0 else "Draw" if max_idx == 1 else "B"
                
                actual_val = req.actualResult
                if not actual_val:
                    actual_val = pick if req.isCorrect else ("B" if pick == "A" else "A")
                
                p["actualResult"] = actual_val
                p["actualScore"] = "Manual"
                p["rps"] = 0.0 if req.isCorrect else 1.0
                found = True
                
                # Resolve in user SQLite db
                db.resolve_user_pronostics(p["teamA"], p["teamB"], actual_val)
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
                        
                        # Resolve user official pronostics
                        db.resolve_user_pronostics(team_a, team_b, actual)
                        
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
# ============================================================
# CRUD DE ANÁLISIS DE IA
# ============================================================
AI_ANALYSES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "ai_analyses.json")

def _require_admin_password():
    if not ADMIN_PASSWORD:
        raise HTTPException(status_code=503, detail="ADMIN_PASSWORD no configurada en el servidor.")

class VerifyAuthRequest(BaseModel):
    password: str

class AIAnalysisRequest(BaseModel):
    id: Optional[int] = None
    teamA: str
    teamB: str
    analysisText: str
    keyTips: List[str]
    confidence: int
    predictedScore: str
    modelName: str
    stage: Optional[str] = "Fase de Grupos"
    keyPlayers: Optional[str] = ""
    oddsA: Optional[float] = None
    oddsDraw: Optional[float] = None
    oddsB: Optional[float] = None
    odds: Optional[dict] = None

@app.post("/api/ai-auth/verify")
@limiter.limit("10/minute")
def verify_auth(request: Request, req: VerifyAuthRequest):
    _require_admin_password()
    if req.password == ADMIN_PASSWORD:
        return {"status": "success", "message": "Authenticated successfully"}
    raise HTTPException(status_code=401, detail="Contraseña incorrecta")

@app.get("/api/ai-analyses")
def get_ai_analyses():
    try:
        analyses = db.db_get_all_ai_analyses()
        return {"analyses": analyses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai-analyses/{team_a}/{team_b}")
def get_ai_analysis_for_match(team_a: str, team_b: str):
    try:
        analysis = db.db_get_ai_analysis(team_a, team_b)
        if analysis:
            return {"status": "success", "analysis": analysis}
        return {"status": "not_found", "message": "No AI analysis found for this match-up."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai-analyses")
def save_ai_analysis(req: AIAnalysisRequest, x_admin_password: Optional[str] = Header(None)):
    _require_admin_password()
    if not x_admin_password or x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta o no autorizada")
    try:
        saved_entry = db.db_save_ai_analysis(req.dict())
        return {"status": "success", "analysis": saved_entry}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/ai-analyses/{analysis_id}")
def delete_ai_analysis(analysis_id: int, x_admin_password: Optional[str] = Header(None)):
    _require_admin_password()
    if not x_admin_password or x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta o no autorizada")
    try:
        deleted = db.db_delete_ai_analysis(analysis_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Analysis not found.")
        return {"status": "success", "message": "Analysis deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# SUPABASE JWT VERIFICATION
# ============================================================
import urllib.request
import urllib.error

def _require_supabase_auth():
    if not SUPABASE_URL or not SUPABASE_PUBLISHABLE_KEY:
        raise HTTPException(status_code=503, detail="Supabase Auth no configurado en el servidor.")

def _require_supabase_admin():
    if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Supabase service role no configurada (SUPABASE_SECRET_KEY).")

def get_current_user_from_supabase(authorization: Optional[str] = Header(None)):
    _require_supabase_auth()
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = authorization.split(" ")[1]
    
    req_url = f"{SUPABASE_URL}/auth/v1/user"
    req = urllib.request.Request(req_url)
    req.add_header("apikey", SUPABASE_PUBLISHABLE_KEY)
    req.add_header("Authorization", f"Bearer {token}")
    
    try:
        with urllib.request.urlopen(req) as response:
            user_data = json.loads(response.read().decode("utf-8"))
            return user_data
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=401, detail="Invalid token or session expired")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")

class LookupUsernameRequest(BaseModel):
    username: str

@app.post("/api/lookup-username")
def lookup_username(req: LookupUsernameRequest):
    _require_supabase_admin()
    req_url = f"{SUPABASE_URL}/auth/v1/admin/users"
    request = urllib.request.Request(req_url)
    request.add_header("apikey", SUPABASE_SECRET_KEY)
    request.add_header("Authorization", f"Bearer {SUPABASE_SECRET_KEY}")
    
    try:
        with urllib.request.urlopen(request) as response:
            users_data = json.loads(response.read().decode("utf-8"))
            if isinstance(users_data, dict) and "users" in users_data:
                users = users_data["users"]
            else:
                users = users_data
                
            for u in users:
                if isinstance(u, dict):
                    meta = u.get("user_metadata", {})
                    if meta.get("username") == req.username or meta.get("display_name") == req.username:
                        return {"status": "success", "email": u.get("email")}
                        
            return {"status": "not_found", "message": "Username not found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error looking up user: {str(e)}")

# ============================================================
# ADMIN USER MANAGEMENT
# ============================================================
class UpdateUserPlanRequest(BaseModel):
    plan: str

@app.get("/api/admin/users")
def get_admin_users(x_admin_password: Optional[str] = Header(None)):
    _require_admin_password()
    if not x_admin_password or x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta o no autorizada")
    _require_supabase_admin()

    req_url = f"{SUPABASE_URL}/auth/v1/admin/users"
    request = urllib.request.Request(req_url)
    request.add_header("apikey", SUPABASE_SECRET_KEY)
    request.add_header("Authorization", f"Bearer {SUPABASE_SECRET_KEY}")
    
    try:
        with urllib.request.urlopen(request) as response:
            users_data = json.loads(response.read().decode("utf-8"))
            if isinstance(users_data, dict) and "users" in users_data:
                users = users_data["users"]
            else:
                users = users_data
            
            result_users = []
            for u in users:
                if isinstance(u, dict):
                    meta = u.get("user_metadata", {}) or {}
                    result_users.append({
                        "id": u.get("id"),
                        "email": u.get("email"),
                        "username": meta.get("username") or meta.get("display_name") or (u.get("email") or "").split("@")[0],
                        "created_at": u.get("created_at"),
                        "plan": (meta.get("plan") or "FREE").upper()
                    })
            return {"status": "success", "users": result_users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing users: {str(e)}")

@app.put("/api/admin/users/{user_id}/plan")
def update_user_plan(user_id: str, req: UpdateUserPlanRequest, x_admin_password: Optional[str] = Header(None)):
    _require_admin_password()
    if not x_admin_password or x_admin_password != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta o no autorizada")
    _require_supabase_admin()

    req_url = f"{SUPABASE_URL}/auth/v1/admin/users/{user_id}"
    
    # 1. Fetch user to retrieve current metadata
    get_request = urllib.request.Request(req_url)
    get_request.add_header("apikey", SUPABASE_SECRET_KEY)
    get_request.add_header("Authorization", f"Bearer {SUPABASE_SECRET_KEY}")
    
    current_meta = {}
    try:
        with urllib.request.urlopen(get_request) as response:
            user_info = json.loads(response.read().decode("utf-8"))
            current_meta = user_info.get("user_metadata", {}) or {}
    except Exception as e:
        pass
    
    # 2. Update plan in metadata
    current_meta["plan"] = req.plan.upper()
    
    req_data = json.dumps({"user_metadata": current_meta}).encode("utf-8")
    put_request = urllib.request.Request(req_url, data=req_data, method="PUT")
    put_request.add_header("apikey", SUPABASE_SECRET_KEY)
    put_request.add_header("Authorization", f"Bearer {SUPABASE_SECRET_KEY}")
    put_request.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(put_request) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return {"status": "success", "user": res_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating user plan: {str(e)}")

# Pydantic models for user endpoints
class FavoriteRequest(BaseModel):
    teamA: str
    teamB: str
    xgA: float
    xgB: float
    probWinA: float
    probDraw: float
    probWinB: float
    notes: Optional[str] = ""

class PresetRequest(BaseModel):
    presetName: str
    fifaWeight: float
    h2hWeight: float
    decayMonths: float
    strengthOverrideA: float
    strengthOverrideB: float
    altitude: int

class VoteRequest(BaseModel):
    teamA: str
    teamB: str
    vote: str # 'A', 'Draw', or 'B'

class PronosticRequest(BaseModel):
    teamA: str
    teamB: str
    guess: str # 'A', 'Draw', or 'B'

@app.post("/api/user/favorites")
def add_user_favorite(req: FavoriteRequest, authorization: Optional[str] = Header(None)):
    user_data = get_current_user_from_supabase(authorization)
    user_id = user_data["id"]
    fav_id = db.add_favorite(
        user_id=user_id,
        team_a=req.teamA,
        team_b=req.teamB,
        xg_a=req.xgA,
        xg_b=req.xgB,
        prob_a=req.probWinA,
        prob_draw=req.probDraw,
        prob_b=req.probWinB,
        notes=req.notes
    )
    return {"status": "success", "favorite_id": fav_id}

@app.get("/api/user/favorites")
def get_user_favorites(authorization: Optional[str] = Header(None)):
    user_data = get_current_user_from_supabase(authorization)
    user_id = user_data["id"]
    favs = db.get_user_favorites(user_id)
    return {"status": "success", "favorites": favs}

@app.delete("/api/user/favorites/{favorite_id}")
def delete_user_favorite(favorite_id: int, authorization: Optional[str] = Header(None)):
    user_data = get_current_user_from_supabase(authorization)
    user_id = user_data["id"]
    success = db.delete_favorite(user_id, favorite_id)
    if not success:
        raise HTTPException(status_code=404, detail="Favorite not found or not owned by user")
    return {"status": "success", "message": "Favorite deleted successfully"}

@app.post("/api/user/presets")
def add_user_preset(req: PresetRequest, authorization: Optional[str] = Header(None)):
    user_data = get_current_user_from_supabase(authorization)
    user_id = user_data["id"]
    preset_id = db.add_user_preset(
        user_id=user_id,
        preset_name=req.presetName,
        fifa_weight=req.fifaWeight,
        h2h_weight=req.h2hWeight,
        decay=req.decayMonths,
        override_a=req.strengthOverrideA,
        override_b=req.strengthOverrideB,
        altitude=req.altitude
    )
    return {"status": "success", "preset_id": preset_id}

@app.get("/api/user/presets")
def get_user_presets(authorization: Optional[str] = Header(None)):
    user_data = get_current_user_from_supabase(authorization)
    user_id = user_data["id"]
    presets = db.get_user_presets(user_id)
    return {"status": "success", "presets": presets}

@app.delete("/api/user/presets/{preset_id}")
def delete_user_preset(preset_id: int, authorization: Optional[str] = Header(None)):
    user_data = get_current_user_from_supabase(authorization)
    user_id = user_data["id"]
    success = db.delete_user_preset(user_id, preset_id)
    if not success:
        raise HTTPException(status_code=404, detail="Preset not found or not owned by user")
    return {"status": "success", "message": "Preset deleted successfully"}

@app.post("/api/match/vote")
def cast_match_vote(req: VoteRequest, authorization: Optional[str] = Header(None)):
    user_data = get_current_user_from_supabase(authorization)
    user_id = user_data["id"]
    match_key = db.get_match_key(req.teamA, req.teamB)
    success = db.cast_vote(match_key, user_id, req.vote)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to cast vote")
    return {"status": "success", "message": "Vote recorded successfully"}

@app.get("/api/match/vote/{team_a}/{team_b}")
def get_match_vote(team_a: str, team_b: str, authorization: Optional[str] = Header(None)):
    match_key = db.get_match_key(team_a, team_b)
    stats = db.get_match_votes_stats(match_key)
    
    # Optional: get user's vote if user is authenticated
    user_vote = None
    if authorization and authorization.startswith("Bearer "):
        try:
            user_data = get_current_user_from_supabase(authorization)
            user_vote = db.get_user_vote_for_match(match_key, user_data["id"])
        except Exception:
            pass # Silent fail if auth is invalid for this read-only request
            
    return {
        "status": "success",
        "stats": stats,
        "user_vote": user_vote
    }

@app.post("/api/match/pronostic")
def cast_match_pronostic(req: PronosticRequest, authorization: Optional[str] = Header(None)):
    user_data = get_current_user_from_supabase(authorization)
    user_id = user_data["id"]
    # Get username from metadata or email
    meta = user_data.get("user_metadata") or {}
    username = meta.get("username") or meta.get("display_name") or user_data.get("email", "Usuario").split("@")[0]
    
    success = db.register_official_pronostic(
        user_id=user_id,
        username=username,
        team_a=req.teamA,
        team_b=req.teamB,
        guess=req.guess
    )
    if not success:
        raise HTTPException(status_code=400, detail="Ya has registrado un pronóstico pendiente para este partido.")
    return {"status": "success", "message": "Pronóstico oficial registrado."}

@app.get("/api/match/pronostic/{team_a}/{team_b}")
def get_match_pronostic(team_a: str, team_b: str, authorization: Optional[str] = Header(None)):
    user_data = get_current_user_from_supabase(authorization)
    user_id = user_data["id"]
    pronostic = db.get_user_match_pronostic(user_id, team_a, team_b)
    return {"status": "success", "pronostic": pronostic}

@app.get("/api/leaderboard")
def get_leaderboard():
    rankings = db.get_leaderboard_rankings()
    return {"status": "success", "leaderboard": rankings}



app.include_router(equipo_router)

# Mount static files (HTML, CSS, JS) at the end, so it doesn't mask API routes
app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend"), html=True), name="static")

if __name__ == "__main__":
    import socket
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    port = int(os.environ.get("PORT", 3000))
    local_ip = get_local_ip()
    
    print("\n" + "="*65)
    print("  PREDICTOR MUNDIAL 2026 - SERVIDOR ACTIVO")
    print(f"  -> En tu computadora, abre: http://localhost:{port}")
    if local_ip != "127.0.0.1":
        print(f"  -> En tu teléfono (mismo Wi-Fi): http://{local_ip}:{port}")
    else:
        print("  -> Conéctate a una red Wi-Fi para habilitar el acceso móvil.")
    print("="*65 + "\n")
    
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
