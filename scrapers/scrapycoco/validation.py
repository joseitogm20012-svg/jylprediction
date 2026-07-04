from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime


class PreviewWarning(BaseModel):
    row: int
    field: str
    message: str
    severity: str = "warning"


class PreviewResult(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    total: int
    warnings: list[PreviewWarning] = []


def _is_empty(v):
    return v is None or str(v).strip() == ""

def _is_number(v):
    try:
        float(v)
        return True
    except (ValueError, TypeError):
        return False

def _invalid_date(v):
    if v is None or str(v).strip() == "":
        return False
    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M"]:
        try:
            datetime.strptime(str(v).strip(), fmt)
            return False
        except ValueError:
            continue
    return True

def _to_float(v):
    try:
        return float(v)
    except (ValueError, TypeError):
        return None

def _to_int(v):
    try:
        return int(v)
    except (ValueError, TypeError):
        return None

VALIDATION_RULES = {
    "results": [
        ("home_score", lambda v: v is not None and (not _is_number(v) or float(v) < 0), "Goles local negativo"),
        ("away_score", lambda v: v is not None and (not _is_number(v) or float(v) < 0), "Goles visitante negativo"),
        ("home_team", _is_empty, "Equipo local vacío"),
        ("away_team", _is_empty, "Equipo visitante vacío"),
        ("date", lambda v: _is_empty(v) or _invalid_date(v), "Fecha inválida"),
    ],
    "xg": [
        ("team", _is_empty, "Equipo vacío"),
        ("xg_for", lambda v: v is not None and _to_float(v) is not None and _to_float(v) < 0, "xG negativo"),
        ("xg_for", lambda v: v is not None and _to_float(v) is not None and _to_float(v) > 20, "xG fuera de rango (>20)"),
    ],
    "xga": [
        ("team", _is_empty, "Equipo vacío"),
        ("xg_against", lambda v: v is not None and _to_float(v) is not None and _to_float(v) < 0, "xGA negativo"),
    ],
    "cards": [
        ("team", _is_empty, "Equipo vacío"),
        ("yellow_cards", lambda v: v is not None and _to_int(v) is not None and _to_int(v) < 0, "Tarjetas amarillas negativo"),
        ("red_cards", lambda v: v is not None and _to_int(v) is not None and _to_int(v) < 0, "Tarjetas rojas negativo"),
    ],
    "flashscore": [
        ("match_id", _is_empty, "ID de partido vacío"),
        ("home_team", _is_empty, "Equipo local vacío"),
        ("away_team", _is_empty, "Equipo visitante vacío"),
    ],
    "transfermarkt": [
        ("team", _is_empty, "Equipo vacío"),
        ("market_value", lambda v: v is not None and _to_float(v) is not None and _to_float(v) < 0, "Valor de mercado negativo"),
    ],
    "wc2026": [],
    "elo": [],
}


def validate_rows(scraper_id: str, rows: list[dict]) -> PreviewResult:
    if not rows:
        return PreviewResult(columns=[], rows=[], total=0, warnings=[])
    columns = list(set(k for r in rows for k in r.keys()))
    warnings = []
    rules = VALIDATION_RULES.get(scraper_id, [])

    seen = {}
    for i, row in enumerate(rows):
        key = str(sorted(row.items()))
        if key in seen:
            warnings.append(PreviewWarning(
                row=i, field="(all)",
                message=f"Fila duplicada de la fila {seen[key]}",
                severity="warning"
            ))
        else:
            seen[key] = i

    for i, row in enumerate(rows):
        for field, check_fn, msg in rules:
            val = row.get(field)
            if check_fn(val):
                severity = "error" if ("negativo" in msg or "vacío" in msg) else "warning"
                warnings.append(PreviewWarning(row=i, field=field, message=msg, severity=severity))

    for i, row in enumerate(rows):
        for col in columns:
            if _is_empty(row.get(col)):
                if not any(w.row == i and w.field == col for w in warnings):
                    warnings.append(PreviewWarning(row=i, field=col, message="Valor nulo", severity="warning"))

    warnings.sort(key=lambda w: (w.row, w.field))
    return PreviewResult(columns=columns, rows=rows[:50], total=len(rows), warnings=warnings)
