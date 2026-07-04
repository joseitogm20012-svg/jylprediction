import json
import logging
from datetime import datetime, timezone
from typing import Optional

from models.base import SessionLocal
from models.execution import ExecutionHistory

logger = logging.getLogger(__name__)


class QualityReport:
    def __init__(self, scraper_id: str, source: str = ""):
        self.scraper_id = scraper_id
        self.source = source
        self.total_items = 0
        self.valid_count = 0
        self.invalid_count = 0
        self.duplicates_removed = 0
        self.normalized_count = 0
        self.validation_errors: list[dict] = []
        self.validation_warnings: list[dict] = []
        self.start_time = datetime.now(timezone.utc)
        self.end_time: Optional[datetime] = None
        self.elapsed_ms: Optional[int] = None
        self.item_types: dict[str, int] = {}

    def track_item(self, item_type: str):
        self.item_types[item_type] = self.item_types.get(item_type, 0) + 1
        self.total_items += 1

    def track_valid(self):
        self.valid_count += 1

    def track_invalid(self):
        self.invalid_count += 1

    def track_duplicate(self):
        self.duplicates_removed += 1

    def track_normalized(self):
        self.normalized_count += 1

    def add_validation_issue(self, field: str, message: str, severity: str = "warning"):
        entry = {"field": field, "message": message}
        if severity == "error":
            self.validation_errors.append(entry)
        else:
            self.validation_warnings.append(entry)

    def finish(self):
        self.end_time = datetime.now(timezone.utc)
        delta = self.end_time - self.start_time
        self.elapsed_ms = int(delta.total_seconds() * 1000)

    @property
    def score(self):
        if self.total_items == 0:
            return 100.0
        clean = self.total_items - self.invalid_count - self.duplicates_removed
        return round((clean / self.total_items) * 100, 1)

    @property
    def summary(self):
        return {
            "scraper_id": self.scraper_id,
            "source": self.source,
            "total_items": self.total_items,
            "valid": self.valid_count,
            "invalid": self.invalid_count,
            "duplicates_removed": self.duplicates_removed,
            "normalized": self.normalized_count,
            "validation_errors": len(self.validation_errors),
            "validation_warnings": len(self.validation_warnings),
            "quality_score": self.score,
            "elapsed_ms": self.elapsed_ms,
            "item_types": self.item_types,
        }

    def to_dict(self):
        return {
            **self.summary,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "validation_errors": self.validation_errors[:50],
            "validation_warnings": self.validation_warnings[:50],
        }


class QualityTracker:
    def __init__(self):
        self._reports: dict[str, QualityReport] = {}

    def start(self, scraper_id: str, source: str = "") -> QualityReport:
        report = QualityReport(scraper_id, source)
        self._reports[scraper_id] = report
        return report

    def get(self, scraper_id: str) -> Optional[QualityReport]:
        return self._reports.get(scraper_id)

    def finish(self, scraper_id: str) -> Optional[QualityReport]:
        report = self._reports.get(scraper_id)
        if report:
            report.finish()
        return report

    def get_stats(self) -> dict:
        return {sid: r.summary for sid, r in self._reports.items()}

    def get_overall(self) -> dict:
        total = sum(r.total_items for r in self._reports.values())
        valid = sum(r.valid_count for r in self._reports.values())
        invalid = sum(r.invalid_count for r in self._reports.values())
        dups = sum(r.duplicates_removed for r in self._reports.values())
        errors = sum(len(r.validation_errors) for r in self._reports.values())
        score = round((valid / total) * 100, 1) if total > 0 else 100.0
        return {
            "total_items": total,
            "valid": valid,
            "invalid": invalid,
            "duplicates_removed": dups,
            "total_validation_errors": errors,
            "overall_quality_score": score,
            "scrapers_tracked": len(self._reports),
        }


quality_tracker = QualityTracker()


def save_quality_report(report: QualityReport, session=None):
    """Persiste un quality report como metadata de una execution_history."""
    own_session = session is None
    if own_session:
        session = SessionLocal()
    try:
        entry = ExecutionHistory(
            scraper_id=report.scraper_id,
            status="quality_check",
            started_at=report.start_time.isoformat(),
            finished_at=report.end_time.isoformat() if report.end_time else None,
            duration_ms=report.elapsed_ms,
            records_count=report.total_items,
            metadata_json=json.dumps(report.to_dict(), ensure_ascii=False),
        )
        session.add(entry)
        if own_session:
            session.commit()
    finally:
        if own_session:
            session.close()
