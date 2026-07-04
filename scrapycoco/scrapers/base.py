import sys
import time
import json
import random
from pathlib import Path
from datetime import datetime, timezone

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0"
]


class BaseScraper:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.sandbox = False
        self.preview_mode = False
        self._preview_data = None
        self._structured_logs = []
        self.validation_errors = []
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"

    def log(self, message: str):
        try:
            print(message)
        except UnicodeEncodeError:
            try:
                print(message.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
            except Exception:
                print(message.encode('ascii', errors='replace').decode('ascii'))

        if self.log_callback:
            self.log_callback(message)

    def structured_log(self, level: str, message: str, **extra):
        data = {
            "level": level,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **extra
        }
        self._structured_logs.append(data)
        json_str = json.dumps(data, ensure_ascii=False)
        try:
            print(f"[{level.upper()}] {message}")
        except Exception:
            pass
        if self.log_callback:
            self.log_callback(json_str)

    def log_info(self, message: str, **extra):
        self.structured_log("info", message, **extra)

    def log_warning(self, message: str, **extra):
        self.structured_log("warning", message, **extra)

    def log_error(self, message: str, **extra):
        self.structured_log("error", message, **extra)

    def log_success(self, message: str, **extra):
        self.structured_log("success", message, **extra)

    def get_random_user_agent(self) -> str:
        return random.choice(USER_AGENTS)

    def sleep_random(self, min_sec=1.5, max_sec=4.0):
        sec = random.uniform(min_sec, max_sec)
        time.sleep(sec)

    def set_preview_mode(self, active: bool = True):
        self.preview_mode = active
        if active:
            self.sandbox = True

    def set_preview_data(self, data: list[dict]):
        self._preview_data = data

    def get_preview_data(self) -> list[dict]:
        return self._preview_data or []

    def validate_and_report(self, row: dict, scraper_id: str):
        try:
            from validation import VALIDATION_RULES
            rules = VALIDATION_RULES.get(scraper_id, [])
            from validation import _is_empty
            for field, check_fn, msg in rules:
                val = row.get(field)
                if check_fn(val):
                    err = {
                        "level": "validation_warning",
                        "message": msg + f": {val}",
                        "row": len(self.validation_errors),
                        "field": field,
                        "value": str(val) if val is not None else "null",
                        "severity": "error" if ("negativo" in msg or "vacío" in msg) else "warning"
                    }
                    self.validation_errors.append(err)
                    self.structured_log(**err)
        except ImportError:
            pass

    def run_diagnostic(self, page_source: str, url: str = "") -> dict:
        from bs4 import BeautifulSoup
        import diagnostic as diag
        import db

        soup = BeautifulSoup(page_source, "html.parser")
        snapshot = diag.take_snapshot(soup, url)

        last = db.get_latest_snapshot(self.__class__.__name__)
        if last:
            import json
            old = diag.dict_to_snapshot(json.loads(last["snapshot"]))
            diff = diag.compare_snapshots(old, snapshot)
            has_changes = diff.has_changes
            severity = diff.severity
            changes = [{"selector": i.selector_key, "type": i.change_type,
                        "old": i.old_value, "new": i.new_value, "severity": i.severity} for i in diff.items]
            if has_changes:
                self.structured_log("diagnostic", f"Cambios estructurales detectados ({severity})",
                                    change_count=len(changes), severity=severity)
        else:
            has_changes = False
            severity = "none"
            changes = []

        db.save_snapshot(
            scraper_id=self.__class__.__name__,
            snapshot_json=json.dumps(diag.snapshot_to_dict(snapshot), ensure_ascii=False),
            html_hash=snapshot.html_hash,
            url=url
        )

        return {
            "has_changes": has_changes,
            "severity": severity,
            "changes": changes,
            "snapshot": diag.snapshot_to_dict(snapshot),
            "tab_labels": snapshot.tab_labels,
            "table_count": snapshot.table_count,
            "class_hashes": snapshot.class_hashes
        }

    def run(self, **kwargs):
        if "sandbox" in kwargs:
            self.sandbox = bool(kwargs.pop("sandbox"))
        if "preview" in kwargs:
            self.preview_mode = bool(kwargs.pop("preview"))
            if self.preview_mode:
                self.sandbox = True
        if type(self) is BaseScraper:
            raise NotImplementedError("Cada scraper debe implementar el método run()")
