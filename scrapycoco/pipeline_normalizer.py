import re
from datetime import datetime

TEAM_ALIASES = {
    "Manchester Utd": "Manchester United",
    "Man Utd": "Manchester United",
    "Man United": "Manchester United",
    "Manchester City": "Manchester City",
    "Man City": "Manchester City",
    "Tottenham": "Tottenham Hotspur",
    "Spurs": "Tottenham Hotspur",
    "Wolves": "Wolverhampton Wanderers",
    "Newcastle": "Newcastle United",
    "Leicester": "Leicester City",
    "Nott'm Forest": "Nottingham Forest",
    "Sheffield Utd": "Sheffield United",
    "Sheffield Wed": "Sheffield Wednesday",
    "West Ham": "West Ham United",
    "Brighton": "Brighton & Hove Albion",
    "Napoli": "SSC Napoli",
    "AC Milan": "AC Milan",
    "Inter": "Inter Milan",
    "Inter Milan": "Inter Milan",
    "Juventus": "Juventus",
    "Roma": "AS Roma",
    "Lazio": "SS Lazio",
    "Atalanta": "Atalanta",
    "Barcelona": "FC Barcelona",
    "Real Madrid": "Real Madrid",
    "Atletico Madrid": "Atlético Madrid",
    "Atlético": "Atlético Madrid",
    "Sevilla": "Sevilla",
    "Valencia": "Valencia",
    "Villarreal": "Villarreal",
    "Real Betis": "Real Betis",
    "Athletic Club": "Athletic Bilbao",
    "Athletic Bilbao": "Athletic Bilbao",
    "Bayern Munich": "Bayern München",
    "Bayern München": "Bayern München",
    "Dortmund": "Borussia Dortmund",
    "Borussia Dortmund": "Borussia Dortmund",
    "Leverkusen": "Bayer Leverkusen",
    "Bayer Leverkusen": "Bayer Leverkusen",
    "Leipzig": "RB Leipzig",
    "RB Leipzig": "RB Leipzig",
    "Monaco": "AS Monaco",
    "PSG": "Paris Saint-Germain",
    "Paris Saint-Germain": "Paris Saint-Germain",
    "Marseille": "Olympique Marseille",
    "Olympique Marseille": "Olympique Marseille",
    "Lyon": "Olympique Lyonnais",
    "Lille": "LOSC Lille",
    "Benfica": "SL Benfica",
    "Porto": "FC Porto",
    "Sporting CP": "Sporting CP",
    "Ajax": "Ajax",
    "PSV": "PSV Eindhoven",
    "Feyenoord": "Feyenoord",
    "Galatasaray": "Galatasaray",
    "Fenerbahçe": "Fenerbahçe",
    "Besiktas": "Beşiktaş",
    "Celtic": "Celtic",
    "Rangers": "Rangers",
    "Club Brugge": "Club Brugge",
    "Shakhtar": "Shakhtar Donetsk",
    "Dynamo Kyiv": "Dynamo Kyiv",
    "Salzburg": "Red Bull Salzburg",
    "Red Bull Salzburg": "Red Bull Salzburg",
    "Köln": "1. FC Köln",
    "Gladbach": "Borussia Mönchengladbach",
}

COMPETITION_ALIASES = {
    "Premier League": "Premier League",
    "EPL": "Premier League",
    "English Premier League": "Premier League",
    "Barclays Premier League": "Premier League",
    "La Liga": "La Liga",
    "LaLiga": "La Liga",
    "Liga BBVA": "La Liga",
    "Serie A": "Serie A",
    "Serie A TIM": "Serie A",
    "Bundesliga": "Bundesliga",
    "Bundesliga 1": "Bundesliga",
    "Ligue 1": "Ligue 1",
    "Ligue 1 Uber Eats": "Ligue 1",
    "Liga Portugal": "Liga Portugal",
    "Primeira Liga": "Liga Portugal",
    "Eredivisie": "Eredivisie",
    "Jupiler Pro League": "Belgian Pro League",
    "Scottish Premiership": "Scottish Premiership",
    "Süper Lig": "Süper Lig",
    "Super Lig": "Süper Lig",
    "Russian Premier League": "Russian Premier League",
    "UEFA Champions League": "UEFA Champions League",
    "Champions League": "UEFA Champions League",
    "UCL": "UEFA Champions League",
    "UEFA Europa League": "UEFA Europa League",
    "Europa League": "UEFA Europa League",
    "UEL": "UEFA Europa League",
    "UEFA Conference League": "UEFA Conference League",
    "Conference League": "UEFA Conference League",
    "UECL": "UEFA Conference League",
    "Copa del Rey": "Copa del Rey",
    "FA Cup": "FA Cup",
    "DFB-Pokal": "DFB-Pokal",
    "Coppa Italia": "Coppa Italia",
    "Coupe de France": "Coupe de France",
    "World Cup": "FIFA World Cup",
    "FIFA World Cup": "FIFA World Cup",
    "Copa America": "Copa América",
    "Copa América": "Copa América",
    "African Cup of Nations": "Africa Cup of Nations",
    "AFCON": "Africa Cup of Nations",
    "Euro": "UEFA European Championship",
    "European Championship": "UEFA European Championship",
    "UEFA Euro": "UEFA European Championship",
}


def normalize_team_name(name: str) -> str:
    if not name:
        return ""
    name = name.strip()
    name = re.sub(r"\s+", " ", name)
    if name in TEAM_ALIASES:
        name = TEAM_ALIASES[name]
    name = name.replace("_", " ").replace("  ", " ")
    name = re.sub(r"[^\w\s.\-&'áéíóúàèìòùâêîôûäëïöüñçÁÉÍÓÚÀÈÌÒÙÂÊÎÔÛÄËÏÖÜÑÇ]", "", name)
    return name.strip()


def normalize_competition_name(name: str) -> str:
    if not name:
        return ""
    name = name.strip()
    if name in COMPETITION_ALIASES:
        return COMPETITION_ALIASES[name]
    return name


def normalize_season(season: str) -> str:
    if not season:
        now = datetime.now()
        year = now.year
        if now.month >= 7:
            return f"{year}-{year + 1}"
        return f"{year - 1}-{year}"
    season = season.replace("/", "-")
    m = re.match(r"(\d{4})", season)
    if m:
        start = int(m.group(1))
        if "-" in season:
            end_str = season.split("-")[1]
            m2 = re.match(r"(\d{4})", end_str)
            if m2:
                return f"{start}-{int(m2.group(1))}"
        return f"{start}-{start + 1}"
    return season


def normalize_position(pos: str) -> str:
    if not pos:
        return ""
    pos = pos.strip().lower()
    mapping = {
        "gk": "Goalkeeper", "goalkeeper": "Goalkeeper", "goalie": "Goalkeeper", "portero": "Goalkeeper",
        "def": "Defender", "defender": "Defender", "df": "Defender", "defensa": "Defender",
        "cb": "Defender", "lb": "Defender", "rb": "Defender",
        "mid": "Midfielder", "midfielder": "Midfielder", "mf": "Midfielder", "centrocampista": "Midfielder",
        "cm": "Midfielder", "cdm": "Midfielder", "cam": "Midfielder",
        "fw": "Forward", "forward": "Forward", "striker": "Forward", "delantero": "Forward",
        "st": "Forward", "cf": "Forward", "lw": "Forward", "rw": "Forward", "ss": "Forward",
    }
    return mapping.get(pos, pos.capitalize())


def normalize_row(item_type: str, row: dict) -> dict:
    result = dict(row)

    if "home_team" in result:
        result["home_team"] = normalize_team_name(result["home_team"])
    if "away_team" in result:
        result["away_team"] = normalize_team_name(result["away_team"])
    if "team" in result:
        result["team"] = normalize_team_name(result["team"])
    if "player_name" in result:
        result["player_name"] = result["player_name"].strip()
    if "competition" in result:
        result["competition"] = normalize_competition_name(result["competition"])
    if "season" in result:
        result["season"] = normalize_season(result["season"])
    if "position" in result:
        result["position"] = normalize_position(result["position"])
    if "formation" in result:
        result["formation"] = result["formation"].strip()

    return result


def normalize_batch(item_type: str, rows: list[dict]) -> list[dict]:
    return [normalize_row(item_type, r) for r in rows]
