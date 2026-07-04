import re
from datetime import datetime
from typing import Any, Optional

FIELD_RULES = {
    "home_team": {"type": str, "min_len": 2, "max_len": 50, "required": True},
    "away_team": {"type": str, "min_len": 2, "max_len": 50, "required": True},
    "home_goals": {"type": int, "min": 0, "max": 50, "nullable": True},
    "away_goals": {"type": int, "min": 0, "max": 50, "nullable": True},
    "match_date": {"type": "date", "required": False, "nullable": True},
    "competition": {"type": str, "min_len": 2, "max_len": 100},
    "season": {"type": str, "pattern": r"^\d{4}-\d{4}$"},
    "status": {"type": str, "choices": ["scheduled", "live", "completed", "postponed", "cancelled"]},
    "player_name": {"type": str, "min_len": 2, "max_len": 60},
    "position": {"type": str, "choices": ["Goalkeeper", "Defender", "Midfielder", "Forward"]},
    "minutes_played": {"type": int, "min": 0, "max": 150},
    "goals": {"type": int, "min": 0, "max": 20},
    "assists": {"type": int, "min": 0, "max": 20},
    "xg": {"type": float, "min": 0.0, "max": 10.0},
    "xa": {"type": float, "min": 0.0, "max": 10.0},
    "shots": {"type": int, "min": 0, "max": 30},
    "shots_on_target": {"type": int, "min": 0, "max": 20},
    "tackles": {"type": int, "min": 0, "max": 30},
    "interceptions": {"type": int, "min": 0, "max": 30},
    "fouls": {"type": int, "min": 0, "max": 20},
    "yellow_card": {"type": int, "min": 0, "max": 2},
    "red_card": {"type": int, "min": 0, "max": 1},
    "rating": {"type": float, "min": 0.0, "max": 10.0},
    "home_odd": {"type": float, "min": 1.01, "max": 100.0},
    "draw_odd": {"type": float, "min": 1.01, "max": 100.0},
    "away_odd": {"type": float, "min": 1.01, "max": 100.0},
    "points": {"type": int, "min": 0, "max": 120},
    "played": {"type": int, "min": 0, "max": 50},
    "won": {"type": int, "min": 0, "max": 50},
    "drawn": {"type": int, "min": 0, "max": 50},
    "lost": {"type": int, "min": 0, "max": 50},
    "goals_for": {"type": int, "min": 0, "max": 200},
    "goals_against": {"type": int, "min": 0, "max": 200},
    "goal_diff": {"type": int, "min": -200, "max": 200},
    "venue": {"type": str, "max_len": 100},
    "referee": {"type": str, "max_len": 100},
    "attendance": {"type": int, "min": 0, "max": 200000},
    "formation": {"type": str, "pattern": r"^\d-\d-\d$"},
    "shirt_number": {"type": int, "min": 1, "max": 99},
}


class ValidationError:
    def __init__(self, field: str, message: str, severity: str = "warning"):
        self.field = field
        self.message = message
        self.severity = severity

    def to_dict(self):
        return {"field": self.field, "message": self.message, "severity": self.severity}


class ValidationReport:
    def __init__(self):
        self.errors: list[ValidationError] = []
        self.warnings: list[ValidationError] = []
        self.total_checked = 0
        self.passed = 0
        self.failed = 0

    @property
    def is_clean(self):
        return len(self.errors) == 0

    @property
    def score(self):
        if self.total_checked == 0:
            return 100.0
        return round((self.passed / self.total_checked) * 100, 1)

    def merge(self, other):
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.total_checked += other.total_checked
        self.passed += other.passed
        self.failed += other.failed


def validate_field(value: Any, rules: dict, field_name: str) -> list[ValidationError]:
    issues = []

    if value is None:
        if rules.get("required"):
            issues.append(ValidationError(field_name, "Campo requerido pero nulo", "error"))
        elif not rules.get("nullable", True):
            issues.append(ValidationError(field_name, "No puede ser nulo", "error"))
        return issues

    expected_type = rules.get("type")
    if expected_type and expected_type != "date":
        if expected_type == int:
            try:
                value = int(value)
            except (ValueError, TypeError):
                issues.append(ValidationError(field_name, f"Debe ser entero, recibido {type(value).__name__}", "error"))
                return issues
        elif expected_type == float:
            try:
                value = float(value)
            except (ValueError, TypeError):
                issues.append(ValidationError(field_name, f"Debe ser decimal, recibido {type(value).__name__}", "error"))
                return issues

    if "min" in rules and isinstance(value, (int, float)):
        if value < rules["min"]:
            issues.append(ValidationError(field_name, f"Valor {value} por debajo del mínimo {rules['min']}", "error"))

    if "max" in rules and isinstance(value, (int, float)):
        if value > rules["max"]:
            issues.append(ValidationError(field_name, f"Valor {value} sobrepasa el máximo {rules['max']}", "warning"))

    if "min_len" in rules and isinstance(value, str):
        if len(value.strip()) < rules["min_len"]:
            issues.append(ValidationError(field_name, f"Longitud {len(value.strip())} < mínimo {rules['min_len']}", "warning"))

    if "max_len" in rules and isinstance(value, str):
        if len(value) > rules["max_len"]:
            issues.append(ValidationError(field_name, f"Longitud {len(value)} > máximo {rules['max_len']}", "warning"))

    if "pattern" in rules and isinstance(value, str):
        if not re.match(rules["pattern"], value.strip()):
            issues.append(ValidationError(field_name, f"No coincide con patrón {rules['pattern']}", "error"))

    if "choices" in rules and isinstance(value, str):
        if value not in rules["choices"]:
            issues.append(ValidationError(field_name, f"'{value}' no es un valor válido. Opciones: {rules['choices']}", "warning"))

    return issues


def validate_item(item_type: str, data: dict) -> ValidationReport:
    report = ValidationReport()
    field_map = {
        "match": ["home_team", "away_team", "home_goals", "away_goals", "match_date", "competition", "season", "status", "venue", "referee", "attendance"],
        "player_stats": ["player_name", "team", "position", "minutes_played", "goals", "assists", "shots", "shots_on_target", "xg", "xa", "tackles", "interceptions", "fouls", "yellow_card", "red_card", "rating"],
        "odds": ["home_odd", "draw_odd", "away_odd"],
        "standing": ["team", "position", "played", "won", "drawn", "lost", "goals_for", "goals_against", "goal_diff", "points"],
        "lineup": ["player_name", "team", "formation", "shirt_number"],
    }

    fields_to_check = field_map.get(item_type, list(data.keys()))
    for field_name in fields_to_check:
        if field_name not in FIELD_RULES:
            continue
        rules = FIELD_RULES[field_name]
        value = data.get(field_name)
        issues = validate_field(value, rules, field_name)
        for issue in issues:
            report.total_checked += 1
            if issue.severity == "error":
                report.errors.append(issue)
                report.failed += 1
            else:
                report.warnings.append(issue)
                report.passed += 1

    if not issues:
        report.total_checked += 1
        report.passed += 1

    return report


def validate_batch(item_type: str, items: list[dict]) -> ValidationReport:
    combined = ValidationReport()
    for item in items:
        report = validate_item(item_type, item)
        combined.merge(report)
    return combined
