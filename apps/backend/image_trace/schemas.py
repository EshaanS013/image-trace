from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CaseCreate(BaseModel):
    case_number: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    analyst_name: str = Field(min_length=1, max_length=160)
    case_timezone: str | None = Field(default=None, max_length=64)


class CasePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    analyst_name: str | None = Field(default=None, min_length=1, max_length=160)
    status: Literal["open", "under_review", "completed", "archived"] | None = None
    case_timezone: str | None = Field(default=None, max_length=64)


class CaseRead(ORMModel):
    id: str
    case_number: str
    name: str
    description: str
    analyst_name: str
    status: str
    case_timezone: str | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None


class Page(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int


class MetadataRead(ORMModel):
    raw_metadata: dict[str, Any]
    datetime_original_raw: str | None
    datetime_digitized_raw: str | None
    gps_datetime_raw: str | None
    timeline_timestamp_raw: str | None
    timeline_timestamp_utc: datetime | None
    timeline_timezone_status: str
    timeline_timestamp_source: str
    timeline_timestamp_confidence: str
    timestamp_selection_reason: str
    gps_latitude: float | None
    gps_longitude: float | None
    gps_altitude: float | None
    camera_make: str | None
    camera_model: str | None
    lens_model: str | None
    software: str | None
    extraction_warnings: list[str]


class EvidenceRead(ORMModel):
    id: str
    case_id: str
    evidence_id: str
    original_filename: str
    mime_type: str
    file_size: int
    width: int
    height: int
    acquired_at: datetime
    acquired_by: str
    sha256_acquisition: str
    sha256_current: str
    integrity_status: str
    review_status: str
    metadata: MetadataRead
    finding_count: int = 0
    highest_severity: str | None = None


class UploadFailure(BaseModel):
    filename: str
    error: str


class UploadResult(BaseModel):
    job_id: str
    accepted: list[EvidenceRead]
    failures: list[UploadFailure]


class ReviewPatch(BaseModel):
    status: Literal["unreviewed", "reviewed", "needs_attention"]
    actor: str = Field(min_length=1, max_length=160)


class NoteCreate(BaseModel):
    actor: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=10000)


class AnalysisCreate(BaseModel):
    travel_speed_threshold_kmh: float = Field(default=1000, ge=1, le=50000)
    editor_patterns: list[str] = Field(default=["photoshop", "gimp", "lightroom"])


class FindingPatch(BaseModel):
    reviewer_status: Literal["acknowledged", "resolved", "excluded"]
    disposition: str = Field(min_length=1, max_length=80)
    actor: str = Field(min_length=1, max_length=160)
    note: str = Field(min_length=1, max_length=5000)


class ReportCreate(BaseModel):
    analysis_run_id: str
    generated_by: str = Field(min_length=1, max_length=160)
    redact_coordinates: bool = True
