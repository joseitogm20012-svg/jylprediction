from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pymongo.errors import PyMongoError

import database
from controllers.equipo_controller import (
    EquipoRepository,
    actualizar_equipo,
    crear_equipo,
    eliminar_equipo,
)
from models.equipo import CONFEDERACIONES

router = APIRouter(prefix="/gestion/equipos", tags=["gestion-equipos"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "views"))
BASE = "/gestion/equipos"


def get_repo() -> EquipoRepository | None:
    try:
        col = database.get_equipos_collection()
        database.ensure_indexes(col)
        return EquipoRepository(col)
    except (database.MongoNoConfiguradoError, PyMongoError):
        return None


def _render_503(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={"mensaje": "MongoDB no configurado o inaccesible. Define MONGODB_URI en el archivo .env"},
        status_code=503,
    )


def _check_repo(repo: EquipoRepository | None, request: Request):
    if repo is None:
        return _render_503(request)
    return None


@router.get("/", response_class=HTMLResponse)
async def lista_equipos(request: Request, repo: EquipoRepository | None = Depends(get_repo)):
    error = _check_repo(repo, request)
    if error:
        return error

    equipos = repo.listar()
    mensaje = request.query_params.get("mensaje")
    return templates.TemplateResponse(
        request=request,
        name="lista.html",
        context={"equipos": equipos, "mensaje": mensaje},
    )


@router.get("/nuevo", response_class=HTMLResponse)
async def nuevo_equipo_form(request: Request, repo: EquipoRepository | None = Depends(get_repo)):
    error = _check_repo(repo, request)
    if error:
        return error

    return templates.TemplateResponse(
        request=request,
        name="formulario.html",
        context={"equipo": None, "confederaciones": CONFEDERACIONES, "errores": [], "accion": f"{BASE}/"},
    )


@router.post("/", response_class=HTMLResponse)
async def crear_equipo_post(request: Request, repo: EquipoRepository | None = Depends(get_repo)):
    error = _check_repo(repo, request)
    if error:
        return error

    form_data = await request.form()
    datos = dict(form_data)
    res = crear_equipo(repo, datos)
    if res.ok:
        return RedirectResponse(url=f"{BASE}/?mensaje={quote(res.mensaje)}", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="formulario.html",
        context={"equipo": datos, "confederaciones": CONFEDERACIONES, "errores": res.errores or [res.mensaje], "accion": f"{BASE}/"},
        status_code=400,
    )


@router.get("/{equipo_id}", response_class=HTMLResponse)
async def detalle_equipo(request: Request, equipo_id: str, repo: EquipoRepository | None = Depends(get_repo)):
    error = _check_repo(repo, request)
    if error:
        return error

    equipo = repo.obtener(equipo_id)
    if equipo is None:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"mensaje": "Equipo no encontrado"},
            status_code=404,
        )

    return templates.TemplateResponse(
        request=request,
        name="detalle.html",
        context={"equipo": equipo},
    )


@router.get("/{equipo_id}/editar", response_class=HTMLResponse)
async def editar_equipo_form(request: Request, equipo_id: str, repo: EquipoRepository | None = Depends(get_repo)):
    error = _check_repo(repo, request)
    if error:
        return error

    equipo = repo.obtener(equipo_id)
    if equipo is None:
        return templates.TemplateResponse(
            request=request,
            name="error.html",
            context={"mensaje": "Equipo no encontrado"},
            status_code=404,
        )

    return templates.TemplateResponse(
        request=request,
        name="formulario.html",
        context={"equipo": equipo, "confederaciones": CONFEDERACIONES, "errores": [], "accion": f"{BASE}/{equipo_id}/editar"},
    )


@router.post("/{equipo_id}/editar", response_class=HTMLResponse)
async def actualizar_equipo_post(request: Request, equipo_id: str, repo: EquipoRepository | None = Depends(get_repo)):
    error = _check_repo(repo, request)
    if error:
        return error

    form_data = await request.form()
    datos = dict(form_data)
    res = actualizar_equipo(repo, equipo_id, datos)
    if res.ok:
        return RedirectResponse(url=f"{BASE}/?mensaje={quote(res.mensaje)}", status_code=303)

    equipo = repo.obtener(equipo_id) or datos
    return templates.TemplateResponse(
        request=request,
        name="formulario.html",
        context={"equipo": equipo, "confederaciones": CONFEDERACIONES, "errores": res.errores or [res.mensaje], "accion": f"{BASE}/{equipo_id}/editar"},
        status_code=400,
    )


@router.post("/{equipo_id}/eliminar", response_class=HTMLResponse)
async def eliminar_equipo_post(request: Request, equipo_id: str, repo: EquipoRepository | None = Depends(get_repo)):
    error = _check_repo(repo, request)
    if error:
        return error

    res = eliminar_equipo(repo, equipo_id)
    return RedirectResponse(url=f"{BASE}/?mensaje={quote(res.mensaje)}", status_code=303)