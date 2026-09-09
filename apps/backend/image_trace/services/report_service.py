import hashlib
from datetime import UTC, datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.orm import Session

from image_trace import __version__

from ..models import (
    AnalysisRun,
    Case,
    CustodyEvent,
    EvidenceFile,
    Finding,
    GeneratedReport,
)
from .storage_service import storage

TEMPLATE_ROOT = Path(__file__).resolve().parents[1] / "templates"
templates = Environment(
    loader=FileSystemLoader(TEMPLATE_ROOT),
    autoescape=select_autoescape(["html"]),
)


def render_html(
    case: Case,
    run: AnalysisRun,
    evidence: list[EvidenceFile],
    findings: list[Finding],
    custody: list[CustodyEvent],
    redact_coordinates: bool = True,
) -> str:
    return templates.get_template("report.html").render(
        case=case,
        run=run,
        evidence=evidence,
        findings=findings,
        custody=custody,
        application_version=__version__,
        generated_at=datetime.now(UTC).isoformat(),
        redact_coordinates=redact_coordinates,
        location_count=sum(1 for item in evidence if item.metadata_record.gps_latitude is not None),
    )


def generate_report(
    db: Session,
    case: Case,
    run: AnalysisRun,
    actor: str,
    redact_coordinates: bool = True,
) -> GeneratedReport:
    if run.case_id != case.id or run.status != "completed":
        raise ValueError("Reports require a completed analysis run for this case")
    evidence = list(
        db.scalars(
            select(EvidenceFile)
            .where(EvidenceFile.case_id == case.id)
            .order_by(EvidenceFile.evidence_id)
        )
    )
    findings = list(
        db.scalars(
            select(Finding).where(Finding.analysis_run_id == run.id).order_by(Finding.created_at)
        )
    )
    custody = list(
        db.scalars(
            select(CustodyEvent)
            .where(CustodyEvent.case_id == case.id)
            .order_by(CustodyEvent.timestamp)
        )
    )
    report = GeneratedReport(
        case_id=case.id,
        analysis_run_id=run.id,
        storage_key="pending",
        sha256="pending",
        manifest_storage_key="pending",
        generated_by=actor,
        application_version=__version__,
    )
    db.add(report)
    db.flush()
    folder = storage.resolve(f"reports/{case.id}")
    folder.mkdir(parents=True, exist_ok=True)
    html_text = render_html(case, run, evidence, findings, custody, redact_coordinates)
    pdf_name = f"{report.id}.pdf"
    pdf_path = folder / pdf_name
    try:
        from weasyprint import HTML  # type: ignore[import-untyped]

        HTML(string=html_text).write_pdf(pdf_path)
    except (ImportError, OSError):
        from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
        from reportlab.pdfgen.canvas import Canvas  # type: ignore[import-untyped]

        canvas = Canvas(str(pdf_path), pagesize=A4)
        canvas.drawString(72, 790, f"IMAGE TRACE report - {case.name}")
        canvas.drawString(72, 770, f"Analysis run: {run.id}")
        canvas.drawString(72, 750, "Printable HTML preview available in the application.")
        canvas.save()
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    manifest_name = f"{report.id}.sha256"
    generated = datetime.now(UTC)
    manifest = "\n".join(
        [
            f"filename={pdf_name}",
            f"sha256={digest}",
            f"generated_at={generated.isoformat()}",
            f"report_id={report.id}",
            f"analysis_run_id={run.id}",
            f"application_version={__version__}",
            "",
        ]
    )
    (folder / manifest_name).write_text(manifest, encoding="utf-8")
    report.storage_key = f"reports/{case.id}/{pdf_name}"
    report.manifest_storage_key = f"reports/{case.id}/{manifest_name}"
    report.sha256 = digest
    report.generated_at = generated
    db.add(
        CustodyEvent(
            case_id=case.id,
            event_type="report_generated",
            actor=actor,
            details_json=f'{{"report_id":"{report.id}","sha256":"{digest}"}}',
        )
    )
    db.commit()
    return report
