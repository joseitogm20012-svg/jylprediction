import re
from datetime import datetime
from typing import Optional

COUNTRY_ALIASES = {
    "USA": "United States", "U.S.A.": "United States", "EE.UU.": "United States",
    "UK": "England", "Inglaterra": "England",
    "Holland": "Netherlands", "Nederland": "Netherlands",
    "South Korea": "Korea Republic", "Korea": "Korea Republic",
    "North Korea": "Korea DPR",
    "Ivory Coast": "Côte d'Ivoire", "Costa de Marfil": "Côte d'Ivoire",
    "Cape Verde": "Cape Verde Islands", "Cabo Verde": "Cape Verde Islands",
    "IR Iran": "Iran", "Rusia": "Russia", "Brasil": "Brazil",
    "Japón": "Japan", "México": "Mexico", "Canadá": "Canada",
    "Panamá": "Panama",
}

DATE_FORMATS = [
    "%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y", "%m/%d/%Y",
    "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M",
    "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S",
]


def to_iso_dates(rows: list[dict], columns: list[str]) -> list[dict]:
    result = []
    for row in rows:
        r = dict(row)
        for col in columns:
            val = r.get(col)
            if val and isinstance(val, str):
                for fmt in DATE_FORMATS:
                    try:
                        dt = datetime.strptime(val.strip(), fmt)
                        r[col] = dt.strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue
        result.append(r)
    return result


def unify_country_names(rows: list[dict], column: str) -> list[dict]:
    result = []
    for row in rows:
        r = dict(row)
        val = r.get(column)
        if val and isinstance(val, str):
            val = val.strip()
            if val in COUNTRY_ALIASES:
                r[column] = COUNTRY_ALIASES[val]
        result.append(r)
    return result


def drop_empty_columns(rows: list[dict]) -> list[dict]:
    if not rows:
        return rows
    columns = list(rows[0].keys())
    keep = [c for c in columns if any(r.get(c) not in (None, "", "N/A", "n/a") for r in rows)]
    return [{k: v for k, v in r.items() if k in keep} for r in rows]


def normalize_team_names(rows: list[dict], column: str) -> list[dict]:
    result = []
    for row in rows:
        r = dict(row)
        val = r.get(column)
        if val and isinstance(val, str):
            name = val.strip().replace("_", " ").replace("-", " ")
            name = re.sub(r'\s+', ' ', name)
            name = re.sub(r'[^\w\sáéíóúàèìòùâêîôûäëïöüñç\'-]', '', name)
            name = name.title()
            for prefix in [" De ", " Del ", " La ", " Los ", " Las ", " Y ", " E "]:
                name = name.replace(prefix, prefix.lower())
            r[column] = name
        result.append(r)
    return result


def _guess_country_columns(columns: list[str]) -> list[str]:
    return [c for c in columns if any(kw in c.lower() for kw in ["team", "country", "nation", "squad", "club", "name"])]


def apply_transforms(rows: list[dict], transforms: list[str]) -> list[dict]:
    if not rows:
        return rows
    columns = list(rows[0].keys())
    result = list(rows)

    for t in transforms:
        if t == "iso_dates":
            result = to_iso_dates(result, columns)
        elif t == "unify_countries":
            for col in _guess_country_columns(columns):
                result = unify_country_names(result, col)
        elif t == "drop_empty":
            result = drop_empty_columns(result)
        elif t == "normalize_teams":
            for col in _guess_country_columns(columns):
                result = normalize_team_names(result, col)

    return result
