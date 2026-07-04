import logging
from typing import Optional

from pipeline_validator import validate_batch, ValidationReport
from pipeline_dedup import dedup, DedupResult
from pipeline_normalizer import normalize_batch
from pipeline_quality import quality_tracker, QualityReport, save_quality_report

logger = logging.getLogger(__name__)


class PipelineResult:
    def __init__(self):
        self.validation: Optional[ValidationReport] = None
        self.dedup: Optional[DedupResult] = None
        self.items_in: int = 0
        self.items_out: int = 0
        self.quality_score: float = 100.0
        self.errors: list[str] = []

    @property
    def success(self):
        return len(self.errors) == 0

    def to_dict(self):
        return {
            "items_in": self.items_in,
            "items_out": self.items_out,
            "duplicates_removed": self.dedup.duplicates_removed if self.dedup else 0,
            "validation_errors": len(self.validation.errors) if self.validation else 0,
            "validation_warnings": len(self.validation.warnings) if self.validation else 0,
            "quality_score": self.quality_score,
            "success": self.success,
            "errors": self.errors,
        }


STAGES = ["validate", "normalize", "dedup"]


def run_pipeline(item_type: str, items: list[dict], scraper_id: str = "",
                 stages: list[str] = None, track_quality: bool = True) -> tuple[list[dict], PipelineResult]:
    if stages is None:
        stages = STAGES

    result = PipelineResult()
    result.items_in = len(items)
    data = list(items)

    if track_quality:
        qr = quality_tracker.start(scraper_id, item_type)

    for stage in stages:
        if stage == "validate":
            vr = validate_batch(item_type, data)
            result.validation = vr
            data = [d for i, d in enumerate(data) if not any(
                e.field == list(d.keys())[0] if list(d.keys()) else False
                for e in vr.errors
            )]
            for d in data:
                if track_quality:
                    qr.track_item(item_type)

        elif stage == "normalize":
            data = normalize_batch(item_type, data)
            if track_quality:
                qr.normalized_count = len(data)

        elif stage == "dedup":
            data, dr = dedup(item_type, data)
            result.dedup = dr
            if track_quality:
                qr.duplicates_removed = dr.duplicates_removed

    result.items_out = len(data)

    if track_quality:
        qr.total_items = result.items_in
        qr.valid_count = result.items_out
        qr.invalid_count = len(result.validation.errors) if result.validation else 0
        qr.finish()
        result.quality_score = qr.score
        save_quality_report(qr)

    logger.info(f"Pipeline {item_type}: {result.items_in} -> {result.items_out} "
                f"(dups={result.dedup.duplicates_removed if result.dedup else 0}, "
                f"score={result.quality_score})")

    return data, result
