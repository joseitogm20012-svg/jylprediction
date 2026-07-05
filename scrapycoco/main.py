import os
import sys
import json
import io
import asyncio
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, Body, Depends, Request
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text

SCRAPYCOCO_DIR = Path(__file__).parent
sys.path.append(str(SCRAPYCOCO_DIR))

from scrapers.fbref import FBrefScraper
from scrapers.flashscore import FlashscoreScraper
from scrapers.transfermarkt import TransfermarktScraper
from scrapers.sofascore import SofascoreScraper
import db
from validation import validate_rows
from export import export_data
from transform import apply_transforms
import scheduler as sched
import diagnostic as diag
from api_security import SecurityHeadersMiddleware, check_rate_limit, rate_limiter
from mongo_db import connect as mongo_connect, disconnect as mongo_disconnect, get_collection_stats
from redis_client import connect as redis_connect, disconnect as redis_disconnect, get_info as redis_info
from api_schemas import (
    ScraperInfo, RunResponse, BatchRunRequest, BatchRunResult,
    HistoryEntry, MetricsResponse, StatsResponse,
    ExportRequest, AddScheduleRequest, ScheduleInfo,
    DiagnosticRequest, DiagnosticResult, CompareResult,
    ScrapySpiderList, PipelineRunResponse, PipelineRunRequest,
    QualitySummary, HealthResponse, SyncRequest,
)

SEVERITY_MAP = {"none": 0, "info": 1, "warning": 2, "critical": 3}

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    await mongo_connect()
    await redis_connect()
    sched.start_scheduler()
    sched.set_executor(_run_single_scraper_internal)
    yield
    sched.stop_scheduler()
    await mongo_disconnect()
    await redis_disconnect()

app = FastAPI(
    title="ScrapyCoco API - Suite de Scraping Modular",
    description="API para scraping de datos de fútbol de múltiples fuentes (FBref, Flashscore, Transfermarkt, Sofascore, OddsPortal). Incluye pipeline de validación, deduplicación, normalización y tracking de calidad.",
    version="2.0.0",
    lifespan=lifespan,
    contact={"name": "JLY Predictor", "url": "https://github.com/jlypredictor/scrapycoco"},
    license_info={"name": "MIT"},
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "System", "description": "Health check y rate limiting"},
        {"name": "Scrapers", "description": "Ejecución y listado de scrapers"},
        {"name": "History", "description": "Historial y métricas de ejecuciones"},
        {"name": "Export", "description": "Exportación de datos en CSV/JSON/XLSX"},
        {"name": "Scheduler", "description": "Gestión de tareas programadas"},
        {"name": "Diagnostic", "description": "Diagnóstico de selectores HTML"},
        {"name": "Scrapy", "description": "Spiders Scrapy avanzados"},
        {"name": "Quality", "description": "Reportes de calidad de datos"},
        {"name": "Pipeline", "description": "Pipeline de validación y normalización"},
    ],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = SCRAPYCOCO_DIR.parent

SCRAPERS = {
    "results": {
        "name": "Actualizar Resultados",
        "description": "Descarga y actualiza results.csv con los últimos resultados de partidos de selecciones.",
        "script": "data/fetch_latest_results.py"
    },
    "xg": {
        "name": "xG, Tiros y Centros (FBref - For)",
        "description": "Scrapea estadísticas ofensivas, disparos, centros y corners a favor desde FBref.",
        "class": FBrefScraper,
        "kwargs": {"type": "xg"}
    },
    "xga": {
        "name": "xGA (FBref - Against)",
        "description": "Scrapea estadísticas defensivas y goles esperados en contra (xGA) desde FBref.",
        "class": FBrefScraper,
        "kwargs": {"type": "xga"}
    },
    "cards": {
        "name": "Tarjetas y Faltas (FBref - Misc)",
        "description": "Scrapea tarjetas amarillas, rojas y faltas cometidas/recibidas desde FBref.",
        "class": FBrefScraper,
        "kwargs": {"type": "cards"}
    },
    "flashscore": {
        "name": "Flashscore Match Stats (Playwright)",
        "description": "Extrae estadísticas en tiempo real (posesión, tiros, faltas) para un partido.",
        "class": FlashscoreScraper
    },
    "transfermarkt": {
        "name": "Transfermarkt Squad Data (Playwright)",
        "description": "Extrae edad promedio, entrenador actual y valor total de la selección.",
        "class": TransfermarktScraper
    },
    "wc2026": {
        "name": "Datos Faltantes Mundial 2026",
        "description": "Completa información faltante de selecciones clasificadas y estadios para el Mundial 2026.",
        "script": "data/fetch_wc2026_missing.py"
    },
    "elo": {
        "name": "Calcular Ratings Elo",
        "description": "Genera ratings Elo calibrados basados en el historial completo de results.csv.",
        "script": "data/generate_elo_ratings.py"
    },
    "shooting": {
        "name": "Tiros por Jugador (FBref - Shooting)",
        "description": "Scrapea estadísticas de tiros, tiros a puerta y goles por jugador desde FBref.",
        "script": "data/fetch_fbref_shooting.py"
    },
    "passing": {
        "name": "Asistencias y Pases (FBref - Standard)",
        "description": "Scrapea asistencias, goles, tarjetas y minutos por jugador desde FBref.",
        "script": "data/fetch_fbref_passing.py"
    },
    "keepers": {
        "name": "Porteros (FBref - Goalkeeping)",
        "description": "Scrapea estadísticas de porteros: vallas invictas, atajadas, goles recibidos desde FBref.",
        "script": "data/fetch_fbref_keepers.py"
    },
    "corners": {
        "name": "Córners por Equipo (FBref - Misc)",
        "description": "Scrapea estadísticas de córners y centros por equipo desde FBref.",
        "script": "data/fetch_fbref_corners.py"
    },
    "sofascore": {
        "name": "Estadísticas Avanzadas (Sofascore)",
        "description": "Extrae datos detallados de tiros, tarjetas y asistencias desde la API de Sofascore.",
        "class": SofascoreScraper
    }

}

tasks_state = {}


def _parse_log_message(msg: str):
    try:
        parsed = json.loads(msg)
        if isinstance(parsed, dict) and "level" in parsed and "message" in parsed:
            return parsed
    except (json.JSONDecodeError, TypeError):
        pass
    return None


async def _run_single_scraper_internal(scraper_id: str, sandbox: bool = False,
                                        match_id: str = None, team_name: str = None,
                                        type: str = None):
    """Plain execution without SSE. Used by scheduler. Returns dict with result."""
    cfg = SCRAPERS.get(scraper_id)
    if not cfg:
        return {"status": "error", "exit_code": -1, "error_message": "Scraper no encontrado"}

    started_at = datetime.now(timezone.utc).isoformat()
    exit_code = 0
    error_message = None

    if "script" in cfg:
        script_path = PROJECT_ROOT / cfg["script"]
        if script_path.exists():
            import subprocess as sp_mod
            def run_sync():
                proc = sp_mod.Popen(
                    [sys.executable, str(script_path)], cwd=str(PROJECT_ROOT),
                    stdout=sp_mod.PIPE, stderr=sp_mod.STDOUT, text=True,
                    creationflags=sp_mod.CREATE_NO_WINDOW if hasattr(sp_mod, 'CREATE_NO_WINDOW') else 0
                )
                for _ in iter(proc.stdout.readline, ''):
                    pass
                proc.wait()
                return proc.returncode
            try:
                exit_code = await asyncio.to_thread(run_sync)
            except Exception as e:
                exit_code = -1
                error_message = f"{type(e).__name__}: {e}"
        else:
            exit_code = -1
            error_message = f"Script no existe: {cfg['script']}"
    elif "class" in cfg:
        kwargs = cfg.get("kwargs", {}).copy()
        if match_id: kwargs["match_id"] = match_id
        if team_name: kwargs["team_name"] = team_name
        if type: kwargs["type"] = type
        kwargs["sandbox"] = sandbox
        instance = cfg["class"]()
        try:
            await asyncio.to_thread(instance.run, **kwargs)
        except Exception as e:
            exit_code = -1
            error_message = f"{type(e).__name__}: {e}"

    finished_at = datetime.now(timezone.utc).isoformat()
    try:
        duration_ms = int((datetime.fromisoformat(finished_at) - datetime.fromisoformat(started_at)).total_seconds() * 1000)
    except Exception:
        duration_ms = None

    status = "success" if exit_code == 0 else "error"
    db.save_execution(scraper_id, status, started_at, finished_at, duration_ms, error_message=error_message, sandbox=sandbox)

    return {"scraper_id": scraper_id, "status": status, "exit_code": exit_code, "error_message": error_message, "duration_ms": duration_ms}


async def _run_single_generator(scraper_id: str, cfg: dict, queue: asyncio.Queue,
                                 thread_safe_log, sandbox: bool,
                                 match_id: str = None, team_name: str = None,
                                 type: str = None, preview: bool = False):
    started_at = datetime.now(timezone.utc).isoformat()
    tasks_state[scraper_id] = {"status": "running", "last_run": started_at, "exit_code": None}
    exit_code = 0
    error_message = None

    try:
        if "script" in cfg:
            script_path = PROJECT_ROOT / cfg["script"]
            if not script_path.exists():
                err = f"El script no existe: {cfg['script']}"
                yield f"event: error\ndata: {json.dumps({'level':'error','message':err,'timestamp':datetime.now(timezone.utc).isoformat()})}\n\n"
                tasks_state[scraper_id]["status"] = "idle"
                tasks_state[scraper_id]["exit_code"] = -1
                db.save_execution(scraper_id, "error", started_at, error_message=err, sandbox=sandbox)
                return
            
            if sandbox:
                thread_safe_log(json.dumps({"level": "info", "message": f"Iniciando simulación sandbox de script legacy: {cfg['script']}", "timestamp": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False))
                await asyncio.sleep(0.1)
                thread_safe_log(json.dumps({"level": "info", "message": "Procesando datos en memoria...", "timestamp": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False))
                await asyncio.sleep(0.1)
                thread_safe_log(json.dumps({"level": "success", "message": "Datos procesados y actualizados exitosamente en sandbox.", "timestamp": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False))
                exit_code = 0
                while not queue.empty():
                    raw = queue.get_nowait()
                    for item in _yield_log(raw): yield item
            else:
                import subprocess as sp_mod
                thread_safe_log(json.dumps({"level":"debug","message":f"DEBUG: sys.exec={sys.executable}, script={script_path}, cwd={PROJECT_ROOT}","timestamp":datetime.now(timezone.utc).isoformat()}, ensure_ascii=False))
                try:
                    def run_subprocess():
                        try:
                            proc = sp_mod.Popen(
                                [sys.executable, str(script_path)], cwd=str(PROJECT_ROOT),
                                stdout=sp_mod.PIPE, stderr=sp_mod.STDOUT, text=True,
                                encoding="utf-8", errors="replace"
                            )
                            for line in iter(proc.stdout.readline, ''):
                                stripped = line.rstrip()
                                if stripped:
                                    thread_safe_log(stripped)
                            proc.wait()
                            return proc.returncode
                        except Exception as e:
                            thread_safe_log(json.dumps({"level":"error","message":f"SUBPROCESS ERROR: {type(e).__name__}: {e}","timestamp":datetime.now(timezone.utc).isoformat()}, ensure_ascii=False))
                            return -2

                    thread_task = asyncio.create_task(asyncio.to_thread(run_subprocess))
                    while not thread_task.done() or not queue.empty():
                        try:
                            raw = await asyncio.wait_for(queue.get(), timeout=0.2)
                            for item in _yield_log(raw): yield item
                        except asyncio.TimeoutError:
                            continue
                    exit_code = thread_task.result()
                except Exception as e:
                    exit_code = -1
                    error_message = f"{type(e).__name__}: {e}"

        elif "class" in cfg:
            scraper_class = cfg["class"]
            scraper_kwargs = cfg.get("kwargs", {}).copy()
            if match_id: scraper_kwargs["match_id"] = match_id
            if team_name: scraper_kwargs["team_name"] = team_name
            if type: scraper_kwargs["type"] = type
            scraper_kwargs["sandbox"] = sandbox
            scraper_kwargs["preview"] = preview

            scraper_instance = scraper_class(log_callback=thread_safe_log)

            async def run_in_thread():
                try:
                    return 0 if await asyncio.to_thread(scraper_instance.run, **scraper_kwargs) else 1
                except Exception as e:
                    thread_safe_log(json.dumps({"level": "error", "message": f"Excepción fatal: {str(e)}", "timestamp": datetime.now(timezone.utc).isoformat()}, ensure_ascii=False))
                    return -1

            thread_task = asyncio.create_task(run_in_thread())
            while not thread_task.done() or not queue.empty():
                try:
                    raw = await asyncio.wait_for(queue.get(), timeout=0.2)
                    for item in _yield_log(raw): yield item
                except asyncio.TimeoutError:
                    continue
            exit_code = thread_task.result()
    except Exception as e:
        exit_code = -1
        error_message = f"{type(e).__name__}: {e}"
    finally:
        finished_at = datetime.now(timezone.utc).isoformat()
        try:
            sd = datetime.fromisoformat(started_at)
            fd = datetime.fromisoformat(finished_at)
            duration_ms = int((fd - sd).total_seconds() * 1000)
        except Exception:
            duration_ms = None

        status = "success" if exit_code == 0 else "error"
        tasks_state[scraper_id] = {"status": "idle", "last_run": started_at, "exit_code": exit_code, "error_message": error_message}

        if not preview:
            db.save_execution(scraper_id, status, started_at, finished_at, duration_ms, error_message=error_message, sandbox=sandbox)

        yield {"scraper_id": scraper_id, "status": status, "exit_code": exit_code, "error_message": error_message, "duration_ms": duration_ms}


def _yield_log(raw: str):
    """Yields appropriate SSE events for a log line. Handles validation_warning specially."""
    parsed = _parse_log_message(raw)
    if parsed:
        level = parsed.get("level", "")
        if level == "validation_warning":
            yield f"event: validation-error\ndata: {raw}\n\n"
        elif level == "diagnostic":
            yield f"event: diagnostic\ndata: {raw}\n\n"
        else:
            yield f"event: log\ndata: {raw}\n\n"
    else:
        yield f"data: {raw}\n\n"


@app.get("/api/health", tags=["System"], summary="Health check", response_model=HealthResponse)
def health_check():
    from scrapy_runner import SPIDER_REGISTRY
    return HealthResponse(
        status="ok", version="2.0.0",
        scrapers_count=len(SCRAPERS),
        spiders_available=list(SPIDER_REGISTRY.keys()),
    )


@app.get("/api/rate-limit", tags=["System"], summary="Ver límite de solicitudes")
def get_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    remaining = rate_limiter.remaining(client_ip)
    return {"client_ip": client_ip, "remaining": remaining, "limit": 60, "window_seconds": 60}


@app.get("/api/infra", tags=["System"], summary="Estado de infraestructura",
         description="Health check de MongoDB, Redis, base de datos SQL y cola de tareas.")
async def infra_status():
    mongo_stats = await get_collection_stats()
    redis_stats = await redis_info()
    from models.base import engine
    sql_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            sql_ok = True
    except Exception:
        pass
    return {
        "sqlite": {"available": sql_ok},
        "mongodb": mongo_stats,
        "redis": redis_stats,
        "queue_pending": redis_stats.get("queue_length", 0) if redis_stats.get("available") else 0,
    }


@app.get("/api/scrapers", tags=["Scrapers"], summary="Listar scrapers disponibles", response_model=list[ScraperInfo])
def list_scrapers():
    result = []
    for k, v in SCRAPERS.items():
        state = tasks_state.get(k, {"status": "idle", "last_run": None, "exit_code": None})
        result.append({"id": k, "name": v["name"], "description": v["description"], **state})
    return result


@app.get("/api/run/{scraper_id}", tags=["Scrapers"], summary="Ejecutar scraper individual",
         description="Ejecuta un scraper por ID con parámetros opcionales. Retorna SSE con logs en tiempo real.")
async def run_scraper(scraper_id: str, match_id: Optional[str] = Query(None),
                       team_name: Optional[str] = Query(None), type: Optional[str] = Query(None),
                       sandbox: bool = Query(False)):
    if scraper_id not in SCRAPERS:
        raise HTTPException(status_code=404, detail="Scraper no encontrado")
    cfg = SCRAPERS[scraper_id]
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def thread_safe_log(msg: str):
        asyncio.run_coroutine_threadsafe(queue.put(msg), loop)

    async def log_generator():
        try:
            yield f"event: start\ndata: {json.dumps({'level':'system','message':f'Iniciando {cfg['name']}...','sandbox':sandbox,'timestamp':datetime.now(timezone.utc).isoformat()})}\n\n"
            async for event in _run_single_generator(scraper_id, cfg, queue, thread_safe_log, sandbox, match_id, team_name, type, preview=False):
                if isinstance(event, str):
                    yield event
        finally:
            st = tasks_state.get(scraper_id, {})
            st_status = st.get("status", "idle")
            ec = st.get("exit_code", -1) if isinstance(st.get("exit_code"), int) else -1
            em = st.get("error_message")
            final_status = "success" if ec == 0 else "error"
            st_msg = "EXITOSO" if ec == 0 else f"FALLIDO (código {ec})" + (f" - {em}" if em else "")
            yield f"event: end\ndata: {json.dumps({'level':final_status,'status':final_status,'message':f'Proceso finalizado. Estado: {st_msg}','exit_code':ec,'error_message':em,'timestamp':datetime.now(timezone.utc).isoformat()})}\n\n"

    return StreamingResponse(log_generator(), media_type="text/event-stream")


@app.post("/api/batch/run", tags=["Scrapers"], summary="Ejecutar scrapers en lote",
          description="Ejecuta múltiples scrapers secuencialmente retornando SSE con progreso.")
async def batch_run(req: BatchRunRequest):
    for sid in req.scraper_ids:
        if sid not in SCRAPERS:
            raise HTTPException(status_code=404, detail=f"Scraper no encontrado: {sid}")
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def thread_safe_log(msg: str):
        asyncio.run_coroutine_threadsafe(queue.put(msg), loop)

    async def batch_generator():
        total = len(req.scraper_ids)
        yield f"event: batch-start\ndata: {json.dumps({'total':total,'sandbox':req.sandbox})}\n\n"
        for idx, sid in enumerate(req.scraper_ids):
            cfg = SCRAPERS[sid]
            yield f"event: batch-progress\ndata: {json.dumps({'completed':idx,'total':total,'current_scraper':sid,'status':'running'})}\n\n"
            yield f"event: start\ndata: {json.dumps({'level':'system','message':f'[{idx+1}/{total}] Iniciando {cfg['name']}...','sandbox':req.sandbox,'timestamp':datetime.now(timezone.utc).isoformat()})}\n\n"
            async for event in _run_single_generator(sid, cfg, queue, thread_safe_log, req.sandbox, req.match_id, req.team_name, preview=False):
                if isinstance(event, str):
                    yield event
            ec = tasks_state.get(sid, {}).get("exit_code", -1)
            yield f"event: batch-progress\ndata: {json.dumps({'completed':idx+1,'total':total,'current_scraper':sid,'status':'success' if ec == 0 else 'error','exit_code':ec})}\n\n"
        c = sum(1 for sid in req.scraper_ids if tasks_state.get(sid, {}).get("exit_code") == 0)
        yield f"event: batch-end\ndata: {json.dumps({'total':total,'completed':c,'failed':total-c})}\n\n"

    return StreamingResponse(batch_generator(), media_type="text/event-stream")


@app.get("/api/preview/{scraper_id}", tags=["Scrapers"], summary="Previsualizar datos de scraper")
async def preview_scraper(scraper_id: str, limit: int = Query(50), sandbox: bool = Query(True),
                           match_id: Optional[str] = Query(None), team_name: Optional[str] = Query(None),
                           type: Optional[str] = Query(None)):
    if scraper_id not in SCRAPERS:
        raise HTTPException(status_code=404, detail="Scraper no encontrado")
    cfg = SCRAPERS[scraper_id]
    if "script" in cfg:
        return JSONResponse({"columns":[],"rows":[],"total":0,"warnings":[{"row":0,"field":"","message":"Preview no soportado para scripts legacy","severity":"warning"}]})
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    def tsl(msg): asyncio.run_coroutine_threadsafe(queue.put(msg), loop)
    sc = cfg["class"]
    kw = cfg.get("kwargs", {}).copy()
    if match_id: kw["match_id"] = match_id
    if team_name: kw["team_name"] = team_name
    if type: kw["type"] = type
    kw["sandbox"] = True; kw["preview"] = True
    inst = sc(log_callback=tsl)
    def rp():
        try:
            inst.run(**kw)
            return inst.get_preview_data()
        except Exception as e:
            return []
    data = await asyncio.to_thread(rp)
    limit = min(limit, 50)
    return JSONResponse(validate_rows(scraper_id, data[:limit] if data else []).model_dump())


@app.get("/api/export/filtered", tags=["Export"], summary="Exportar datos filtrados",
         description="Exporta datos de ejecución filtrados por scraper, estado, con paginación.")
def export_filtered(
    scraper_id: Optional[str] = Query(None),
    format: str = Query("json"),
    status: Optional[str] = Query(None),
    limit: int = Query(1000),
    offset: int = Query(0),
):
    from export import export_data
    import db as db_module
    rows = db_module.get_history(scraper_id, limit, offset)
    if status:
        rows = [r for r in rows if r.get("status") == status]
    count, blob = export_data(rows, format)
    if blob:
        return StreamingResponse(io.BytesIO(blob), media_type="application/octet-stream",
                                 headers={"Content-Disposition": f"attachment; filename=export.{format}"})
    return {"exported": count}


@app.post("/api/export", tags=["Export"], summary="Exportar datos",
          description="Exporta datos de scraper en formato CSV, JSON o XLSX.")
async def export_endpoint(req: ExportRequest):
    if req.scraper_id not in SCRAPERS:
        raise HTTPException(status_code=404, detail="Scraper no encontrado")
    data = req.preview_data
    if data is None:
        cfg = SCRAPERS[req.scraper_id]
        if "script" in cfg:
            raise HTTPException(status_code=400, detail="Export desde scrapers legacy no soportado")
        queue = asyncio.Queue(); loop = asyncio.get_running_loop()
        def tsl(msg): asyncio.run_coroutine_threadsafe(queue.put(msg), loop)
        sc = cfg["class"]; kw = cfg.get("kwargs", {}).copy()
        kw["sandbox"] = True; kw["preview"] = True
        inst = sc(log_callback=tsl)
        def re():
            try:
                inst.run(**kw)
                return inst.get_preview_data()
            except Exception:
                return []
        data = await asyncio.to_thread(re)
    if not data:
        raise HTTPException(status_code=400, detail="No hay datos para exportar")
    if req.transforms:
        data = apply_transforms(data, req.transforms)
    fmt = req.format
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fn = f"{req.scraper_id}_{ts}.{fmt}"
    ext = {"csv":"text/csv","json":"application/json","xlsx":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
    mt = ext.get(fmt, "application/octet-stream")
    cnt, raw = export_data(data, fmt)
    if raw is None:
        p = SCRAPYCOCO_DIR / "exports" / fn; p.parent.mkdir(parents=True, exist_ok=True)
        export_data(data, fmt, path=p)
        return FileResponse(p, media_type=mt, filename=fn)
    return StreamingResponse(iter([raw]), media_type=mt, headers={"Content-Disposition": f'attachment; filename="{fn}"'})


# ── Scheduler Endpoints ──

@app.get("/api/scheduler/list", tags=["Scheduler"], summary="Listar tareas programadas")
def scheduler_list():
    return sched.list_jobs()


@app.post("/api/scheduler/add", tags=["Scheduler"], summary="Agregar tarea programada")
def scheduler_add(req: AddScheduleRequest):
    if req.scraper_id not in SCRAPERS:
        raise HTTPException(status_code=404, detail="Scraper no encontrado")
    db_id = sched.add_job(req.scraper_id, req.cron_expression, req.params)
    return {"id": db_id, "message": "Tarea programada agregada"}


@app.delete("/api/scheduler/{schedule_id}", tags=["Scheduler"], summary="Eliminar tarea programada")
def scheduler_delete(schedule_id: int):
    sched.remove_job(schedule_id)
    return {"message": "Tarea eliminada"}


@app.post("/api/scheduler/{schedule_id}/pause", tags=["Scheduler"], summary="Pausar tarea programada")
def scheduler_pause(schedule_id: int):
    sched.pause_job(schedule_id)
    return {"message": "Tarea pausada"}


@app.post("/api/scheduler/{schedule_id}/resume", tags=["Scheduler"], summary="Reanudar tarea programada")
def scheduler_resume(schedule_id: int):
    sched.resume_job(schedule_id)
    return {"message": "Tarea reanudada"}


@app.post("/api/scheduler/{schedule_id}/run-now", tags=["Scheduler"], summary="Ejecutar tarea inmediatamente")
async def scheduler_run_now(schedule_id: int):
    conn = db.get_conn()
    try:
        row = conn.execute(text("SELECT * FROM schedules WHERE id=:sid"), {"sid": schedule_id}).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    r = dict(row._mapping)
    params = {}
    if r.get("params"):
        try: params = json.loads(r["params"])
        except Exception: pass
    result = await _run_single_scraper_internal(
        r["scraper_id"], sandbox=params.get("sandbox", False),
        match_id=params.get("match_id"), team_name=params.get("team_name")
    )
    return result


# ── Diagnostic Endpoints ──

@app.post("/api/diagnostic/run/{scraper_id}", tags=["Diagnostic"], summary="Ejecutar diagnóstico de scraper")
async def diagnostic_run(scraper_id: str, req: DiagnosticRequest):
    if scraper_id not in SCRAPERS:
        raise HTTPException(status_code=404, detail="Scraper no encontrado")
    cfg = SCRAPERS[scraper_id]
    # If no page_source provided, try to run the scraper to get HTML
    if not req.page_source and "class" in cfg:
        queue = asyncio.Queue(); loop = asyncio.get_running_loop()
        def tsl(msg): asyncio.run_coroutine_threadsafe(queue.put(msg), loop)
        sc = cfg["class"]; kw = cfg.get("kwargs", {}).copy()
        kw["sandbox"] = True; kw["preview"] = True
        inst = sc(log_callback=tsl)
        try:
            await asyncio.to_thread(inst.run, **kw)
        except Exception:
            pass
        # Scrapers store HTML internally in different ways; for now return structure from what we have
        result = {"has_changes": False, "severity": SEVERITY_MAP["none"], "changes": [], "snapshot": {}, "tab_labels": [], "table_count": 0, "class_hashes": {}}
        return JSONResponse(result)
    elif req.page_source:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(req.page_source, "html.parser")
        snapshot = diag.take_snapshot(soup, req.url)
        last = db.get_latest_snapshot(scraper_id)
        has_changes = False
        severity = SEVERITY_MAP["none"]
        changes = []
        if last:
            import json as j2
            old = diag.dict_to_snapshot(j2.loads(last["snapshot"]))
            diff = diag.compare_snapshots(old, snapshot)
            has_changes = diff.has_changes
            severity = SEVERITY_MAP.get(diff.severity, 0)
            changes = [{"selector": i.selector_key, "type": i.change_type,
                        "old": i.old_value, "new": i.new_value, "severity": SEVERITY_MAP.get(i.severity, 0)} for i in diff.items]

        db.save_snapshot(scraper_id, json.dumps(diag.snapshot_to_dict(snapshot), ensure_ascii=False), snapshot.html_hash, req.url)

        return JSONResponse({
            "has_changes": has_changes,
            "severity": severity,
            "changes": changes,
            "snapshot": diag.snapshot_to_dict(snapshot),
            "tab_labels": snapshot.tab_labels,
            "table_count": snapshot.table_count,
            "class_hashes": snapshot.class_hashes
        })
    return JSONResponse({"has_changes": False, "severity": SEVERITY_MAP["none"], "changes": [], "message": "Sin datos para diagnosticar"})


@app.get("/api/diagnostic/history/{scraper_id}", tags=["Diagnostic"], summary="Historial de diagnósticos")
def diagnostic_history(scraper_id: str):
    return db.get_snapshots(scraper_id)


@app.get("/api/diagnostic/compare/{id1}/{id2}", tags=["Diagnostic"], summary="Comparar dos diagnósticos")
def diagnostic_compare(id1: int, id2: int):
    s1 = db.get_snapshot(id1)
    s2 = db.get_snapshot(id2)
    if not s1 or not s2:
        raise HTTPException(status_code=404, detail="Snapshot no encontrado")
    import json as j2
    old = diag.dict_to_snapshot(j2.loads(s1["snapshot"]))
    new = diag.dict_to_snapshot(j2.loads(s2["snapshot"]))
    diff = diag.compare_snapshots(old, new)
    return JSONResponse({
        "has_changes": diff.has_changes, "severity": SEVERITY_MAP.get(diff.severity, 0),
        "changes": [{"selector": i.selector_key, "type": i.change_type,
                      "old": i.old_value, "new": i.new_value, "severity": SEVERITY_MAP.get(i.severity, 0)} for i in diff.items],
        "snapshot_old_id": id1, "snapshot_new_id": id2
    })


# ── History & Static Endpoints ──
@app.get("/api/history", tags=["History"], summary="Historial de ejecuciones",
         response_model=list[HistoryEntry])
def get_history(scraper_id: Optional[str] = Query(None), limit: int = Query(100), offset: int = Query(0)):
    return db.get_history(scraper_id, limit, offset)

@app.get("/api/history/metrics", tags=["History"], summary="Métricas globales de scraping",
         response_model=MetricsResponse)
def get_history_metrics(scraper_id: Optional[str] = Query(None)):
    return db.get_metrics(scraper_id)

@app.get("/api/history/stats", tags=["History"], summary="Estadísticas por scraper",
         response_model=list[StatsResponse])
def get_history_stats():
    return db.get_history_stats()


@app.get("/api/scrapy/spiders", tags=["Scrapy"], summary="Listar spiders Scrapy disponibles",
         response_model=ScrapySpiderList)
def list_scrapy_spiders():
    from scrapy_runner import SPIDER_REGISTRY
    return {"spiders": list(SPIDER_REGISTRY.keys())}


@app.post("/api/scrapy/run/{spider_name}", tags=["Scrapy"], summary="Ejecutar spider Scrapy",
          description="Ejecuta un spider de Scrapy por nombre. Retorna estadísticas de ejecución.")
async def run_scrapy_spider(spider_name: str):
    from scrapy_runner import ScrapyRunner, SPIDER_REGISTRY
    if spider_name not in SPIDER_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Spider '{spider_name}' not found")
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, lambda: ScrapyRunner().run_spider(spider_name))
    return result


@app.post("/api/scrapy/run-all", tags=["Scrapy"], summary="Ejecutar todos los spiders Scrapy",
          description="Ejecuta todos los spiders registrados secuencialmente.")
async def run_all_scrapy_spiders():
    from scrapy_runner import ScrapyRunner
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, lambda: ScrapyRunner().run_all())
    return result


@app.get("/api/quality", tags=["Quality"], summary="Resumen global de calidad",
         response_model=QualitySummary)
def get_quality_overview():
    from pipeline_quality import quality_tracker
    return quality_tracker.get_overall()


@app.get("/api/quality/{scraper_id}", tags=["Quality"], summary="Reporte de calidad por scraper")
def get_quality_report(scraper_id: str):
    from pipeline_quality import quality_tracker
    report = quality_tracker.get(scraper_id)
    if not report:
        return {"detail": "No quality report found for this scraper"}
    return report.to_dict()


@app.post("/api/pipeline/run", tags=["Pipeline"], summary="Ejecutar pipeline de datos",
          description="Ejecuta el pipeline de validación, normalización y deduplicación sobre un conjunto de items.")
async def run_pipeline(payload: PipelineRunRequest):
    from pipeline_orchestrator import run_pipeline as rp
    data, result = rp(payload.item_type, payload.items, payload.scraper_id, payload.stages)
    return {"result": result.to_dict(), "items_out": len(data)}

@app.post("/api/sync", tags=["Scrapers"], summary="Sincronizar datos a Supabase",
          description="Ejecuta la sincronización de datos scrapeados a Supabase PostgreSQL. Permite seleccionar qué datos sincronizar.")
async def sync_to_supabase(req: SyncRequest):
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def thread_safe_log(msg: str):
        asyncio.run_coroutine_threadsafe(queue.put(msg), loop)

    async def sync_generator():
        yield f"event: sync-start\ndata: {json.dumps({'message':'Iniciando sincronización a Supabase...','timestamp':datetime.now(timezone.utc).isoformat()})}\n\n"

        from sync_engine import SyncEngine
        engine = SyncEngine(log_callback=thread_safe_log)
        steps = []
        if req.matches: steps.append(("matches", "Resultados", engine.sync_matches))
        if req.elo: steps.append(("elo", "Ratings Elo", engine.sync_elo))
        if req.team_metrics: steps.append(("team_metrics", "xG y Estadísticas", engine.sync_team_metrics))
        if req.corners_stats: steps.append(("corners_stats", "Córners por equipo", engine.sync_corners_stats))
        if req.match_corners: steps.append(("match_corners", "Córners por partido", engine.sync_match_corners))

        if not steps:
            yield f"event: sync-error\ndata: {json.dumps({'message':'No se seleccionó ningún tipo de datos para sincronizar','timestamp':datetime.now(timezone.utc).isoformat()})}\n\n"
            return

        total = len(steps)
        results = {}
        for idx, (key, name, func) in enumerate(steps):
            yield f"event: sync-progress\ndata: {json.dumps({'completed':idx,'total':total,'current':key,'name':name,'status':'running','timestamp':datetime.now(timezone.utc).isoformat()})}\n\n"
            yield f"event: log\ndata: {json.dumps({'level':'info','message':f'[{idx+1}/{total}] Sincronizando {name}...','timestamp':datetime.now(timezone.utc).isoformat()})}\n\n"

            try:
                def run_sync_step():
                    return func()
                count = await asyncio.to_thread(run_sync_step)
                results[key] = count
                yield f"event: log\ndata: {json.dumps({'level':'success','message':f'[{idx+1}/{total}] {name}: {count} registros sincronizados','timestamp':datetime.now(timezone.utc).isoformat()})}\n\n"
            except Exception as e:
                results[key] = 0
                yield f"event: log\ndata: {json.dumps({'level':'error','message':f'[{idx+1}/{total}] {name}: ERROR - {e}','timestamp':datetime.now(timezone.utc).isoformat()})}\n\n"

            yield f"event: sync-progress\ndata: {json.dumps({'completed':idx+1,'total':total,'current':key,'name':name,'status':'success' if results.get(key,0) > 0 else 'error','timestamp':datetime.now(timezone.utc).isoformat()})}\n\n"

            # Drain queued logs
            while not queue.empty():
                raw = queue.get_nowait()
                yield f"event: log\ndata: {raw}\n\n"

        yield f"event: sync-end\ndata: {json.dumps({'results':results,'message':'Sincronización completada','timestamp':datetime.now(timezone.utc).isoformat()})}\n\n"

    return StreamingResponse(sync_generator(), media_type="text/event-stream")


@app.get("/")
def serve_index():
    return FileResponse(SCRAPYCOCO_DIR / "index.html")

@app.get("/style.css")
def serve_css():
    return FileResponse(SCRAPYCOCO_DIR / "style.css")

@app.get("/script.js")
def serve_js():
    return FileResponse(SCRAPYCOCO_DIR / "script.js")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 3006))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
