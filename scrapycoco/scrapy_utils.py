import re
from datetime import datetime, timedelta

PATTERNS = {
    "score": re.compile(r"(?P<home>\d+)\s*[–:]\s*(?P<away>\d+)"),
    "datetime_iso": re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}"),
    "date_iso": re.compile(r"\d{4}-\d{2}-\d{2}"),
    "date_eu": re.compile(r"\d{2}/\d{2}/\d{4}"),
    "odds_decimal": re.compile(r"\d+\.\d{2}"),
    "odds_fractional": re.compile(r"\d+/\d+"),
    "team_name": re.compile(r"^[A-Za-zÁ-Úá-úÑñ\s\.\-']+$"),
    "formation": re.compile(r"^\d-\d-\d$"),
    "player_name": re.compile(r"^[A-Za-zÁ-Úá-úÑñ\s\.\-']{2,50}$"),
    "competition_year": re.compile(r"\d{4}"),
    "percentage": re.compile(r"(\d+(?:\.\d+)?)\s*%"),
    "money_usd": re.compile(r"\$\s?[\d,]+(?:\.\d{2})?"),
    "money_eur": re.compile(r"€\s?[\d,]+(?:\.\d{2})?"),
    "height_cm": re.compile(r"(\d+)\s*cm"),
    "weight_kg": re.compile(r"(\d+)\s*kg"),
}


def parse_score(text):
    m = PATTERNS["score"].search(text)
    if m:
        return int(m.group("home")), int(m.group("away"))
    return None, None


def parse_odds(text):
    m = PATTERNS["odds_decimal"].search(text)
    if m:
        return float(m.group(0))
    m = PATTERNS["odds_fractional"].search(text)
    if m:
        parts = m.group(0).split("/")
        return float(int(parts[0]) / int(parts[1]) + 1)
    return None


def parse_date(text):
    if not text:
        return None
    text = text.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d %b %Y", "%B %d, %Y",
                "%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def parse_timestamp(ts):
    try:
        return datetime.fromtimestamp(int(ts))
    except (ValueError, TypeError, OSError):
        return None


def clean_team_name(name):
    name = re.sub(r"\s+", " ", name.strip())
    name = re.sub(r"[\(\)\[\]\"]", "", name)
    return name


def clean_player_name(name):
    name = re.sub(r"\s+", " ", name.strip())
    name = re.sub(r"[^\w\s\.\-'áéíóúÁÉÍÓÚñÑ]", "", name)
    return name.strip()


def extract_competition_year(text):
    m = PATTERNS["competition_year"].search(text)
    return int(m.group(0)) if m else datetime.now().year


def normalize_position(pos):
    pos = pos.lower().strip()
    mapping = {
        "gk": "Goalkeeper", "goalkeeper": "Goalkeeper", "goalie": "Goalkeeper",
        "def": "Defender", "defender": "Defender", "df": "Defender",
        "mid": "Midfielder", "midfielder": "Midfielder", "mf": "Midfielder",
        "fw": "Forward", "forward": "Forward", "striker": "Forward",
        "attacker": "Forward", "att": "Forward",
    }
    return mapping.get(pos, pos.capitalize())


def infer_season(now=None):
    if now is None:
        now = datetime.now()
    if now.month >= 7:
        return f"{now.year}-{now.year + 1}"
    return f"{now.year - 1}-{now.year}"


def validate_team_name(name):
    return bool(PATTERNS["team_name"].match(name or ""))


def validate_player_name(name):
    return bool(PATTERNS["player_name"].match(name or ""))
