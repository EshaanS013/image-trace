import json
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from image_trace import __version__

from .database import get_db
from .models import (
    AnalysisRun,
    Case,
    CustodyEvent,
    EvidenceFile,
    EvidenceNote,
    Finding,
    FindingReviewEvent,
    GeneratedReport,
    Job,
)
from .schemas import (
    AnalysisCreate,
    CaseCreate,
    CasePatch,
    FindingPatch,
    NoteCreate,
    ReportCreate,
    ReviewPatch,
)
from .services.analysis_service import run_analysis
from .services.evidence_service import EvidenceError, register_upload, verify_integrity
from .services.geo_service import haversine_km, speed_kmh
from .services.report_service import generate_report, render_html
from .services.storage_service import storage

router = APIRouter(prefix="/api/v1")
Db = Annotated[Session, Depends(get_db)]


def require[T](db: Session, model: type[T], identifier: str) -> T:
    value = db.get(model, identifier)
    if value is None:
        raise HTTPException(
            404, detail={"code": "not_found", "message": "Requested resource was not found"}
        )
    return value


def metadata_json(item: EvidenceFile) -> dict[str, object]:
    meta = item.metadata_record
    return {
        "raw_metadata": json.loads(meta.raw_metadata_json),
        "datetime_original_raw": meta.datetime_original_raw,
        "datetime_digitized_raw": meta.datetime_digitized_raw,
        "gps_datetime_raw": meta.gps_datetime_raw,
        "timeline_timestamp_raw": meta.timeline_timestamp_raw,
        "timeline_timestamp_utc": meta.timeline_timestamp_utc,
        "timeline_timezone_status": meta.timeline_timezone_status,
        "timeline_timestamp_source": meta.timeline_timestamp_source,
        "timeline_timestamp_confidence": meta.timeline_timestamp_confidence,
        "timestamp_selection_reason": meta.timestamp_selection_reason,
        "gps_latitude": meta.gps_latitude,
        "gps_longitude": meta.gps_longitude,
        "gps_altitude": meta.gps_altitude,
        "camera_make": meta.camera_make,
        "camera_model": meta.camera_model,
        "lens_model": meta.lens_model,
        "software": meta.software,
        "extraction_warnings": json.loads(meta.extraction_warnings_json),
    }


def evidence_json(db: Session, item: EvidenceFile) -> dict[str, object]:
    findings = list(db.scalars(select(Finding).where(Finding.evidence_file_id == item.id)))
    priority = {"high": 3, "review": 2, "info": 1}
    highest = max(
        (finding.severity for finding in findings), key=lambda x: priority.get(x, 0), default=None
    )
    return {
        "id": item.id,
        "case_id": item.case_id,
        "evidence_id": item.evidence_id,
        "original_filename": item.original_filename,
        "mime_type": item.mime_type,
        "file_size": item.file_size,
        "width": item.width,
        "height": item.height,
        "acquired_at": item.acquired_at,
        "acquired_by": item.acquired_by,
        "sha256_acquisition": item.sha256_acquisition,
        "sha256_current": item.sha256_current,
        "integrity_status": item.integrity_status,
        "review_status": item.review_status,
        "metadata": metadata_json(item),
        "finding_count": len(findings),
        "highest_severity": highest,
    }


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/version")
def version() -> dict[str, str]:
    return {"version": __version__, "build_commit": "development"}


@router.post("/cases", status_code=201, response_model=None)
def create_case(payload: CaseCreate, db: Db) -> Case:
    case = Case(**payload.model_dump())
    db.add(case)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            409, detail={"code": "duplicate_case_number", "message": "Case number already exists"}
        ) from error
    db.refresh(case)
    return case


@router.get("/cases", response_model=None)
def list_cases(
    db: Db,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: str | None = None,
) -> dict[str, object]:
    query = select(Case)
    count = select(func.count()).select_from(Case)
    if status:
        query, count = query.where(Case.status == status), count.where(Case.status == status)
    items = list(
        db.scalars(
            query.order_by(Case.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
        )
    )
    return {"items": items, "total": db.scalar(count) or 0, "page": page, "page_size": page_size}


@router.get("/cases/{case_id}", response_model=None)
def get_case(case_id: str, db: Db) -> Case:
    return require(db, Case, case_id)


@router.patch("/cases/{case_id}", response_model=None)
def patch_case(case_id: str, payload: CasePatch, db: Db) -> Case:
    case = require(db, Case, case_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(case, key, value)
    if payload.status == "archived":
        case.archived_at = datetime.now(UTC)
    elif payload.status and case.archived_at:
        case.archived_at = None
    if payload.status == "completed":
        case.closed_at = datetime.now(UTC)
    db.commit()
    return case


@router.post("/cases/{case_id}/evidence", status_code=201)
def upload_evidence(
    case_id: str,
    db: Db,
    files: Annotated[list[UploadFile], File()],
    acquired_by: Annotated[str, Form()],
) -> dict[str, object]:
    case = require(db, Case, case_id)
    if len(files) > 200:
        raise HTTPException(
            413, detail={"code": "batch_too_large", "message": "Maximum 200 files per batch"}
        )
    job = Job(
        case_id=case.id,
        job_type="evidence_upload",
        status="running",
        stage="validating",
        total_items=len(files),
        attempt_count=1,
        started_at=datetime.now(UTC),
    )
    db.add(job)
    db.commit()
    accepted, failures = [], []
    for upload in files:
        try:
            job.stage = "preserving"
            item = register_upload(db, case, upload, acquired_by)
            accepted.append(evidence_json(db, item))
            job.completed_items += 1
        except (EvidenceError, OSError, ValueError) as error:
            failures.append({"filename": upload.filename or "unnamed", "error": str(error)})
            job.failed_items += 1
    job.status = (
        "partial_failure" if failures and accepted else "failed" if failures else "completed"
    )
    job.stage = "completed"
    job.completed_at = datetime.now(UTC)
    job.error_summary = f"{len(failures)} file(s) failed" if failures else None
    db.commit()
    return {"job_id": job.id, "accepted": accepted, "failures": failures}


@router.get("/cases/{case_id}/evidence")
def list_evidence(
    case_id: str,
    db: Db,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: str | None = None,
    integrity: str | None = None,
    review: str | None = None,
    sort: str = "created_at",
    order: str = "asc",
) -> dict[str, object]:
    require(db, Case, case_id)
    query = select(EvidenceFile).where(EvidenceFile.case_id == case_id)
    if search:
        query = query.where(
            or_(
                EvidenceFile.original_filename.contains(search),
                EvidenceFile.evidence_id.contains(search),
            )
        )
    if integrity:
        query = query.where(EvidenceFile.integrity_status == integrity)
    if review:
        query = query.where(EvidenceFile.review_status == review)
    column = getattr(EvidenceFile, sort, EvidenceFile.created_at)
    query = query.order_by(column.desc() if order == "desc" else column.asc())
    all_items = list(db.scalars(query))
    items = all_items[(page - 1) * page_size : page * page_size]
    return {
        "items": [evidence_json(db, item) for item in items],
        "total": len(all_items),
        "page": page,
        "page_size": page_size,
    }


@router.get("/evidence/{evidence_id}")
def get_evidence(evidence_id: str, db: Db) -> dict[str, object]:
    return evidence_json(db, require(db, EvidenceFile, evidence_id))


@router.get("/evidence/{evidence_id}/thumbnail")
def thumbnail(evidence_id: str, db: Db) -> FileResponse:
    item = require(db, EvidenceFile, evidence_id)
    _, path = storage.thumbnail_path(item.case_id, item.id)
    return FileResponse(
        path, media_type="image/webp", filename=f"{item.evidence_id}-thumbnail.webp"
    )


@router.get("/evidence/{evidence_id}/download")
def download_evidence(evidence_id: str, db: Db) -> FileResponse:
    item = require(db, EvidenceFile, evidence_id)
    return FileResponse(
        storage.resolve(item.storage_key),
        media_type=item.mime_type,
        filename=item.original_filename,
    )


@router.post("/evidence/{evidence_id}/verify-integrity")
def verify(
    evidence_id: str,
    db: Db,
    actor: str = Query(..., min_length=1, max_length=160),
) -> dict[str, object]:
    return evidence_json(db, verify_integrity(db, require(db, EvidenceFile, evidence_id), actor))


@router.patch("/evidence/{evidence_id}/review")
def review_evidence(evidence_id: str, payload: ReviewPatch, db: Db) -> dict[str, object]:
    item = require(db, EvidenceFile, evidence_id)
    prior = item.review_status
    item.review_status = payload.status
    db.add(
        CustodyEvent(
            case_id=item.case_id,
            evidence_file_id=item.id,
            event_type="evidence_review_changed",
            actor=payload.actor,
            details_json=json.dumps({"prior": prior, "new": payload.status}),
        )
    )
    db.commit()
    return evidence_json(db, item)


@router.post("/evidence/{evidence_id}/notes", status_code=201, response_model=None)
def add_note(evidence_id: str, payload: NoteCreate, db: Db) -> EvidenceNote:
    item = require(db, EvidenceFile, evidence_id)
    note = EvidenceNote(evidence_file_id=item.id, **payload.model_dump())
    db.add(note)
    db.add(
        CustodyEvent(
            case_id=item.case_id,
            evidence_file_id=item.id,
            event_type="note_added",
            actor=payload.actor,
            details_json=json.dumps({"note_id": note.id}),
        )
    )
    db.commit()
    return note


@router.get("/evidence/{evidence_id}/notes", response_model=None)
def notes(evidence_id: str, db: Db) -> list[EvidenceNote]:
    require(db, EvidenceFile, evidence_id)
    return list(
        db.scalars(
            select(EvidenceNote)
            .where(EvidenceNote.evidence_file_id == evidence_id)
            .order_by(EvidenceNote.created_at.desc())
        )
    )


@router.post("/cases/{case_id}/analysis-runs", status_code=201, response_model=None)
def create_analysis(case_id: str, payload: AnalysisCreate, db: Db) -> AnalysisRun:
    require(db, Case, case_id)
    return run_analysis(db, case_id, payload.model_dump())


@router.get("/cases/{case_id}/analysis-runs", response_model=None)
def analyses(case_id: str, db: Db) -> list[AnalysisRun]:
    require(db, Case, case_id)
    return list(
        db.scalars(
            select(AnalysisRun)
            .where(AnalysisRun.case_id == case_id)
            .order_by(AnalysisRun.started_at.desc())
        )
    )


@router.get("/analysis-runs/{analysis_id}", response_model=None)
def analysis(analysis_id: str, db: Db) -> AnalysisRun:
    return require(db, AnalysisRun, analysis_id)


@router.get("/cases/{case_id}/findings", response_model=None)
def findings(
    case_id: str, db: Db, reviewer_status: str | None = None, severity: str | None = None
) -> list[Finding]:
    query = select(Finding).join(AnalysisRun).where(AnalysisRun.case_id == case_id)
    if reviewer_status:
        query = query.where(Finding.reviewer_status == reviewer_status)
    if severity:
        query = query.where(Finding.severity == severity)
    return list(db.scalars(query.order_by(Finding.created_at.desc())))


@router.patch("/findings/{finding_id}", response_model=None)
def patch_finding(finding_id: str, payload: FindingPatch, db: Db) -> Finding:
    finding = require(db, Finding, finding_id)
    prior = finding.reviewer_status
    finding.reviewer_status = payload.reviewer_status
    finding.current_disposition = payload.disposition
    db.add(
        FindingReviewEvent(
            finding_id=finding.id,
            actor=payload.actor,
            prior_status=prior,
            new_status=payload.reviewer_status,
            note=payload.note,
        )
    )
    db.commit()
    return finding


@router.get("/findings/{finding_id}/review-events", response_model=None)
def finding_events(finding_id: str, db: Db) -> list[FindingReviewEvent]:
    require(db, Finding, finding_id)
    return list(
        db.scalars(
            select(FindingReviewEvent)
            .where(FindingReviewEvent.finding_id == finding_id)
            .order_by(FindingReviewEvent.created_at)
        )
    )


@router.get("/cases/{case_id}/timeline")
def timeline(case_id: str, db: Db) -> dict[str, object]:
    items = list(db.scalars(select(EvidenceFile).where(EvidenceFile.case_id == case_id)))
    items.sort(key=lambda i: i.metadata_record.timeline_timestamp_utc or i.acquired_at)
    output, previous = [], None
    for item in items:
        record = evidence_json(db, item)
        record["derived_leg"] = None
        previous_latitude: float | None
        previous_longitude: float | None
        current_latitude: float | None
        current_longitude: float | None
        if previous:
            previous_latitude = previous.metadata_record.gps_latitude
            previous_longitude = previous.metadata_record.gps_longitude
            current_latitude = item.metadata_record.gps_latitude
            current_longitude = item.metadata_record.gps_longitude
        else:
            previous_latitude = None
            previous_longitude = None
            current_latitude = None
            current_longitude = None
        if (
            previous
            and previous_latitude is not None
            and previous_longitude is not None
            and current_latitude is not None
            and current_longitude is not None
        ):
            distance = haversine_km(
                previous_latitude,
                previous_longitude,
                current_latitude,
                current_longitude,
            )
            if (
                previous.metadata_record.timeline_timestamp_utc
                and item.metadata_record.timeline_timestamp_utc
            ):
                seconds = (
                    item.metadata_record.timeline_timestamp_utc
                    - previous.metadata_record.timeline_timestamp_utc
                ).total_seconds()
                record["derived_leg"] = {
                    "distance_km": distance,
                    "interval_seconds": seconds,
                    "speed_kmh": speed_kmh(distance, seconds),
                }
        output.append(record)
        previous = item
    return {"items": output}


@router.get("/cases/{case_id}/map-data")
def map_data(case_id: str, db: Db, redacted: bool = True) -> dict[str, object]:
    items = list(db.scalars(select(EvidenceFile).where(EvidenceFile.case_id == case_id)))
    points = []
    for item in items:
        meta = item.metadata_record
        if meta.gps_latitude is not None and meta.gps_longitude is not None:
            points.append(
                {
                    "evidence_file_id": item.id,
                    "evidence_id": item.evidence_id,
                    "latitude": round(meta.gps_latitude, 2) if redacted else meta.gps_latitude,
                    "longitude": round(meta.gps_longitude, 2) if redacted else meta.gps_longitude,
                    "redacted": redacted,
                    "timestamp": meta.timeline_timestamp_utc,
                }
            )
    points.sort(key=lambda value: str(value["timestamp"]))
    return {"points": points, "online_tiles_enabled": False}


@router.get("/cases/{case_id}/custody-events", response_model=None)
def custody(case_id: str, db: Db) -> list[CustodyEvent]:
    return list(
        db.scalars(
            select(CustodyEvent)
            .where(CustodyEvent.case_id == case_id)
            .order_by(CustodyEvent.timestamp.desc())
        )
    )


@router.get("/jobs/{job_id}", response_model=None)
def job(job_id: str, db: Db) -> Job:
    return require(db, Job, job_id)


@router.post("/jobs/{job_id}/cancel", response_model=None)
def cancel_job(job_id: str, db: Db) -> Job:
    item = require(db, Job, job_id)
    if item.status in {"queued", "running"}:
        item.cancel_requested = True
        item.status = "cancelled"
        item.completed_at = datetime.now(UTC)
    db.commit()
    return item


@router.post("/cases/{case_id}/reports", status_code=201, response_model=None)
def create_report(case_id: str, payload: ReportCreate, db: Db) -> GeneratedReport:
    case = require(db, Case, case_id)
    run = require(db, AnalysisRun, payload.analysis_run_id)
    try:
        return generate_report(db, case, run, payload.generated_by, payload.redact_coordinates)
    except ValueError as error:
        raise HTTPException(
            422, detail={"code": "invalid_analysis_run", "message": str(error)}
        ) from error


@router.get("/cases/{case_id}/reports", response_model=None)
def reports(case_id: str, db: Db) -> list[GeneratedReport]:
    return list(
        db.scalars(
            select(GeneratedReport)
            .where(GeneratedReport.case_id == case_id)
            .order_by(GeneratedReport.generated_at.desc())
        )
    )


@router.get("/reports/{report_id}/preview", response_class=HTMLResponse)
def preview(report_id: str, db: Db) -> str:
    report = require(db, GeneratedReport, report_id)
    case = require(db, Case, report.case_id)
    run = require(db, AnalysisRun, report.analysis_run_id)
    evidence = list(db.scalars(select(EvidenceFile).where(EvidenceFile.case_id == case.id)))
    items = list(db.scalars(select(Finding).where(Finding.analysis_run_id == run.id)))
    events = list(db.scalars(select(CustodyEvent).where(CustodyEvent.case_id == case.id)))
    return render_html(case, run, evidence, items, events)


@router.get("/reports/{report_id}/download")
def report_download(report_id: str, db: Db) -> FileResponse:
    report = require(db, GeneratedReport, report_id)
    return FileResponse(
        storage.resolve(report.storage_key),
        media_type="application/pdf",
        filename=f"image-trace-{report.id}.pdf",
    )


@router.get("/reports/{report_id}/manifest", response_class=PlainTextResponse)
def manifest(report_id: str, db: Db) -> str:
    report = require(db, GeneratedReport, report_id)
    return storage.resolve(report.manifest_storage_key).read_text(encoding="utf-8")
