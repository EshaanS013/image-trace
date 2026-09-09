from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Case(Base):
    __tablename__ = "cases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    case_number: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    analyst_name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(24), default="open", index=True)
    case_timezone: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)
    closed_at: Mapped[datetime | None]
    archived_at: Mapped[datetime | None]
    evidence: Mapped[list[EvidenceFile]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )


class EvidenceFile(Base):
    __tablename__ = "evidence_files"
    __table_args__ = (
        UniqueConstraint("case_id", "evidence_id"),
        Index("idx_evidence_case_created", "case_id", "created_at"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    evidence_id: Mapped[str] = mapped_column(String(40), index=True)
    original_filename: Mapped[str] = mapped_column(String(512))
    storage_key: Mapped[str] = mapped_column(String(256), unique=True)
    mime_type: Mapped[str] = mapped_column(String(80))
    file_size: Mapped[int]
    width: Mapped[int]
    height: Mapped[int]
    acquired_at: Mapped[datetime] = mapped_column(default=utcnow)
    acquired_by: Mapped[str] = mapped_column(String(160))
    sha256_acquisition: Mapped[str] = mapped_column(String(64))
    sha256_current: Mapped[str] = mapped_column(String(64))
    integrity_status: Mapped[str] = mapped_column(String(24), default="verified", index=True)
    review_status: Mapped[str] = mapped_column(String(24), default="unreviewed", index=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)
    case: Mapped[Case] = relationship(back_populates="evidence")
    metadata_record: Mapped[ImageMetadata] = relationship(
        back_populates="evidence", cascade="all, delete-orphan"
    )


class ImageMetadata(Base):
    __tablename__ = "image_metadata"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    evidence_file_id: Mapped[str] = mapped_column(
        ForeignKey("evidence_files.id", ondelete="CASCADE"), unique=True
    )
    raw_metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    datetime_original_raw: Mapped[str | None] = mapped_column(String(128))
    datetime_digitized_raw: Mapped[str | None] = mapped_column(String(128))
    gps_datetime_raw: Mapped[str | None] = mapped_column(String(128))
    timeline_timestamp_raw: Mapped[str | None] = mapped_column(String(128))
    timeline_timestamp_utc: Mapped[datetime | None]
    timeline_timezone_status: Mapped[str] = mapped_column(String(32), default="unknown")
    timeline_timestamp_source: Mapped[str] = mapped_column(
        String(48), default="filesystem_modified"
    )
    timeline_timestamp_confidence: Mapped[str] = mapped_column(String(24), default="low")
    timestamp_selection_reason: Mapped[str] = mapped_column(Text, default="")
    gps_latitude: Mapped[float | None] = mapped_column(Float)
    gps_longitude: Mapped[float | None] = mapped_column(Float)
    gps_altitude: Mapped[float | None] = mapped_column(Float)
    camera_make: Mapped[str | None] = mapped_column(String(160))
    camera_model: Mapped[str | None] = mapped_column(String(160))
    lens_model: Mapped[str | None] = mapped_column(String(160))
    camera_serial_number: Mapped[str | None] = mapped_column(String(160))
    focal_length: Mapped[str | None] = mapped_column(String(80))
    iso: Mapped[str | None] = mapped_column(String(80))
    aperture: Mapped[str | None] = mapped_column(String(80))
    shutter_speed: Mapped[str | None] = mapped_column(String(80))
    software: Mapped[str | None] = mapped_column(String(200))
    width: Mapped[int]
    height: Mapped[int]
    orientation: Mapped[str | None] = mapped_column(String(80))
    extraction_warnings_json: Mapped[str] = mapped_column(Text, default="[]")
    evidence: Mapped[EvidenceFile] = relationship(back_populates="metadata_record")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    analyzer_version: Mapped[str] = mapped_column(String(32))
    rule_set_version: Mapped[str] = mapped_column(String(32))
    application_version: Mapped[str] = mapped_column(String(32))
    build_commit: Mapped[str] = mapped_column(String(64), default="development")
    configuration_json: Mapped[str] = mapped_column(Text)
    configuration_sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(24), index=True)
    started_at: Mapped[datetime] = mapped_column(default=utcnow)
    completed_at: Mapped[datetime | None]
    error_summary: Mapped[str | None] = mapped_column(Text)


class Finding(Base):
    __tablename__ = "findings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    analysis_run_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="CASCADE"), index=True
    )
    evidence_file_id: Mapped[str | None] = mapped_column(
        ForeignKey("evidence_files.id", ondelete="CASCADE"), index=True
    )
    related_evidence_file_id: Mapped[str | None] = mapped_column(
        ForeignKey("evidence_files.id", ondelete="SET NULL")
    )
    category: Mapped[str] = mapped_column(String(48), index=True)
    severity: Mapped[str] = mapped_column(String(24), index=True)
    rule_id: Mapped[str] = mapped_column(String(80))
    rule_version: Mapped[str] = mapped_column(String(24))
    title: Mapped[str] = mapped_column(String(240))
    explanation: Mapped[str] = mapped_column(Text)
    supporting_data_json: Mapped[str] = mapped_column(Text)
    reviewer_status: Mapped[str] = mapped_column(String(24), default="unreviewed", index=True)
    current_disposition: Mapped[str | None] = mapped_column(String(48))
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class FindingReviewEvent(Base):
    __tablename__ = "finding_review_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    finding_id: Mapped[str] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"), index=True
    )
    actor: Mapped[str] = mapped_column(String(160))
    prior_status: Mapped[str] = mapped_column(String(24))
    new_status: Mapped[str] = mapped_column(String(24))
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


class EvidenceNote(Base):
    __tablename__ = "evidence_notes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    evidence_file_id: Mapped[str] = mapped_column(
        ForeignKey("evidence_files.id", ondelete="CASCADE"), index=True
    )
    actor: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow)


class CustodyEvent(Base):
    __tablename__ = "chain_of_custody_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    evidence_file_id: Mapped[str | None] = mapped_column(
        ForeignKey("evidence_files.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    actor: Mapped[str] = mapped_column(String(160))
    timestamp: Mapped[datetime] = mapped_column(default=utcnow)
    details_json: Mapped[str] = mapped_column(Text, default="{}")


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    job_type: Mapped[str] = mapped_column(String(48))
    status: Mapped[str] = mapped_column(String(24), index=True)
    stage: Mapped[str] = mapped_column(String(48))
    total_items: Mapped[int] = mapped_column(Integer, default=0)
    completed_items: Mapped[int] = mapped_column(Integer, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, default=0)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    error_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    started_at: Mapped[datetime | None]
    completed_at: Mapped[datetime | None]


class GeneratedReport(Base):
    __tablename__ = "generated_reports"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    analysis_run_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_runs.id", ondelete="RESTRICT"), index=True
    )
    storage_key: Mapped[str] = mapped_column(String(256), unique=True)
    sha256: Mapped[str] = mapped_column(String(64))
    manifest_storage_key: Mapped[str] = mapped_column(String(256))
    generated_at: Mapped[datetime] = mapped_column(default=utcnow)
    generated_by: Mapped[str] = mapped_column(String(160))
    application_version: Mapped[str] = mapped_column(String(32))
    build_commit: Mapped[str] = mapped_column(String(64), default="development")
