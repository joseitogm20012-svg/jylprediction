from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# --- Scrapers ---

class ScraperInfo(BaseModel):
    id: str
    name: str
    description: str
    status: str
    last_run: Optional[str] = None
    exit_code: Optional[int] = None


class RunResponse(BaseModel):
    scraper: str
    elapsed_seconds: float
    pages_crawled: int
    items_scraped: int
    errors: int


class BatchRunRequest(BaseModel):
    scraper_ids: list[str] = Field(default_factory=list)
    sandbox: bool = False
    match_id: Optional[str] = None
    team_name: Optional[str] = None


class BatchRunResult(BaseModel):
    scraper: str
    status: str
    elapsed_seconds: float
    records_count: int
    error: Optional[str] = None


# --- History ---

class HistoryEntry(BaseModel):
    id: int
    scraper_id: str
    status: str
    started_at: str
    finished_at: Optional[str] = None
    duration_ms: Optional[int] = None
    records_count: int = 0
    error_message: Optional[str] = None
    sandbox: bool = False


class MetricsResponse(BaseModel):
    total_runs: int
    success_count: int
    error_count: int
    avg_duration_ms: Optional[float] = None
    total_records: int
    first_run: Optional[str] = None
    last_run: Optional[str] = None


class StatsResponse(BaseModel):
    scraper_id: str
    total_runs: int
    success_count: int
    error_count: int
    avg_duration_ms: Optional[float] = None
    total_records: int
    last_run: Optional[str] = None


# --- Export ---

class ExportRequest(BaseModel):
    scraper_id: Optional[str] = Field(default=None, description="Filtrar por scraper")
    format: str = Field(default="csv", pattern="^(csv|json|xlsx)$")
    transforms: list[str] = Field(default_factory=list)
    preview_data: Optional[list[dict]] = None
    status: Optional[str] = Field(default=None, description="Filtrar por estado")
    limit: int = Field(default=1000, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)


class AddScheduleRequest(BaseModel):
    scraper_id: str
    cron_expression: str = Field(default="0 6 * * *", description="Expresión cron")
    params: Optional[dict] = None


class DiagnosticRequest(BaseModel):
    url: str = ""
    page_source: Optional[str] = None


# --- Scheduler ---

class ScheduleAddRequest(BaseModel):
    scraper_id: str
    cron_expression: str = Field(default="0 6 * * *", description="Formato cron (min hour day month weekday)")
    params: dict = Field(default_factory=dict)


class ScheduleInfo(BaseModel):
    id: int
    scraper_id: str
    cron_expression: str
    paused: bool
    next_run: Optional[str] = None
    last_run: Optional[str] = None
    params: dict = Field(default_factory=dict)


# --- Diagnostic ---

class DiagnosticResult(BaseModel):
    scraper_id: str
    selector_count: int
    active_selectors: int
    broken_selectors: int
    warnings: list[dict] = Field(default_factory=list)


class CompareResult(BaseModel):
    id1: int
    id2: int
    differences: list[dict] = Field(default_factory=list)
    similarity_pct: float = 0.0


# --- Scrapy ---

class ScrapySpiderList(BaseModel):
    spiders: list[str]


class PipelineRunRequest(BaseModel):
    item_type: str = Field(default="match", pattern="^(match|player_stats|odds|standing|lineup)$")
    items: list[dict] = Field(default_factory=list)
    scraper_id: str = "api"
    stages: list[str] = Field(default=["validate", "normalize", "dedup"])


class PipelineResultResponse(BaseModel):
    items_in: int
    items_out: int
    duplicates_removed: int
    validation_errors: int
    validation_warnings: int
    quality_score: float
    success: bool
    errors: list[str]


class PipelineRunResponse(BaseModel):
    result: PipelineResultResponse
    items_out: list[dict]


# --- Quality ---

class QualitySummary(BaseModel):
    total_items: int
    valid: int
    invalid: int
    duplicates_removed: int
    total_validation_errors: int
    overall_quality_score: float
    scrapers_tracked: int


# --- Common ---

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    scrapers_count: int = 0
    spiders_available: list[str] = Field(default_factory=list)

class SyncRequest(BaseModel):
    matches: bool = False
    elo: bool = False
    team_metrics: bool = False
    corners_stats: bool = False
    match_corners: bool = False
