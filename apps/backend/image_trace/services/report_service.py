import hashlib
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Any

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


def render_fallback_pdf(
    pdf_path: Path,
    case: Case,
    run: AnalysisRun,
    evidence: list[EvidenceFile],
    findings: list[Finding],
    custody: list[CustodyEvent],
    redact_coordinates: bool,
) -> None:
    """Create the full report with ReportLab when WeasyPrint's native stack is unavailable."""
    from reportlab.lib import colors  # type: ignore[import-untyped]
    from reportlab.lib.enums import TA_CENTER  # type: ignore[import-untyped]
    from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
    from reportlab.lib.styles import getSampleStyleSheet  # type: ignore[import-untyped]
    from reportlab.lib.units import mm  # type: ignore[import-untyped]
    from reportlab.platypus import (  # type: ignore[import-untyped]
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    styles = getSampleStyleSheet()
    styles["Title"].textColor = colors.HexColor("#17212b")
    styles["Title"].fontSize = 24
    styles["Title"].leading = 28
    styles["Heading2"].textColor = colors.HexColor("#315d8a")
    styles["Heading2"].spaceBefore = 11
    styles["Heading2"].spaceAfter = 7
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 13
    small = styles["BodyText"].clone("Small")
    small.fontSize = 7
    small.leading = 9
    small.alignment = TA_CENTER

    def paragraph(value: object, style: object = styles["BodyText"]) -> object:
        return Paragraph(escape(str(value)), style)

    def report_table(rows: list[list[object]], widths: list[float]) -> object:
        table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef5")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17212b")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("LEADING", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.HexColor("#f8fafc")],
                    ),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return table

    story: list[object] = [
        paragraph("IMAGE TRACE / VERSIONED ANALYSIS REPORT", styles["Heading3"]),
        paragraph(case.name, styles["Title"]),
        Spacer(1, 4 * mm),
        report_table(
            [
                ["Case", "Analyst", "Analysis run"],
                [
                    paragraph(case.case_number),
                    paragraph(case.analyst_name),
                    paragraph(run.id, small),
                ],
                ["Rule set", "Application", "Build"],
                [run.rule_set_version, __version__, run.build_commit],
            ],
            [55 * mm, 55 * mm, 60 * mm],
        ),
        paragraph("Scope and methodology", styles["Heading2"]),
        paragraph(case.description or "No additional scope description supplied."),
        paragraph(
            "IMAGE TRACE preserves registered originals, computes SHA-256 acquisition hashes, "
            "extracts available metadata, selects timestamps using a documented priority, and "
            "applies transparent versioned rules. Derived routes and speeds use selected values."
        ),
        paragraph(
            "Qualified review required. Automated results are indicators, not conclusions. "
            "Missing metadata is not suspicious by itself, and metadata tags do not establish "
            "authenticity or manipulation."
        ),
        paragraph("Evidence inventory", styles["Heading2"]),
        paragraph(
            f"{len(evidence)} item(s); "
            f"{sum(value.metadata_record.gps_latitude is not None for value in evidence)} with "
            "usable "
            f"GPS metadata. Coordinates are {'redacted' if redact_coordinates else 'included'}."
        ),
    ]
    evidence_rows: list[list[object]] = [
        ["Evidence", "Filename", "Selected time", "Source", "Integrity", "Acquisition SHA-256"]
    ]
    for evidence_item in evidence:
        meta = evidence_item.metadata_record
        digest = " ".join(
            evidence_item.sha256_acquisition[index : index + 16] for index in range(0, 64, 16)
        )
        evidence_rows.append(
            [
                paragraph(evidence_item.evidence_id, small),
                paragraph(evidence_item.original_filename, small),
                paragraph(meta.timeline_timestamp_raw or "-", small),
                paragraph(meta.timeline_timestamp_source, small),
                paragraph(evidence_item.integrity_status, small),
                paragraph(digest, small),
            ]
        )
    story.extend(
        [
            report_table(evidence_rows, [22 * mm, 34 * mm, 35 * mm, 29 * mm, 20 * mm, 30 * mm]),
            PageBreak(),
            paragraph("Findings and review", styles["Heading2"]),
        ]
    )
    finding_rows: list[list[object]] = [
        ["Severity", "Rule", "Finding and explanation", "Review state"]
    ]
    for finding in findings:
        finding_rows.append(
            [
                paragraph(finding.severity, small),
                paragraph(f"{finding.rule_id} v{finding.rule_version}", small),
                paragraph(f"{finding.title}. {finding.explanation}", small),
                paragraph(finding.reviewer_status, small),
            ]
        )
    if not findings:
        finding_rows.append(["-", "-", "No automated findings were generated.", "-"])
    story.extend(
        [
            report_table(finding_rows, [20 * mm, 36 * mm, 88 * mm, 26 * mm]),
            paragraph("Chain of custody", styles["Heading2"]),
        ]
    )
    custody_rows: list[list[object]] = [["Time", "Event", "Actor", "Evidence"]]
    for event in custody:
        custody_rows.append(
            [
                paragraph(event.timestamp.isoformat(), small),
                paragraph(event.event_type, small),
                paragraph(event.actor, small),
                paragraph(event.evidence_file_id or "case", small),
            ]
        )
    story.extend(
        [
            report_table(custody_rows, [42 * mm, 40 * mm, 38 * mm, 50 * mm]),
            paragraph("Limitations", styles["Heading2"]),
            paragraph(
                "Metadata may be missing, inaccurate, altered by ordinary software, or stripped "
                "during transfer. A matching hash verifies byte identity with the acquired copy, "
                "not the truth of image content. Camera grouping relies on reported metadata. "
                "Location and travel values are derived, not observations."
            ),
        ]
    )

    def page_footer(canvas: Any, document: Any) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#52606d"))
        canvas.drawString(20 * mm, 10 * mm, f"Analysis run {run.id}")
        canvas.drawRightString(190 * mm, 10 * mm, f"Page {document.page}")
        canvas.restoreState()

    document = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"IMAGE TRACE report - {case.case_number}",
        author=case.analyst_name,
    )
    document.build(story, onFirstPage=page_footer, onLaterPages=page_footer)


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
        render_fallback_pdf(pdf_path, case, run, evidence, findings, custody, redact_coordinates)
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
