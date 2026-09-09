import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from image_trace import __version__

from ..models import AnalysisRun, EvidenceFile, Finding
from .geo_service import haversine_km, speed_kmh
from .timeline_service import parse_exif_datetime

RULE_SET_VERSION = "1.1.0"
RULE_VERSION = "1.0"


def add_finding(
    db: Session,
    run: AnalysisRun,
    evidence: EvidenceFile,
    rule_id: str,
    category: str,
    severity: str,
    title: str,
    explanation: str,
    support: dict[str, object],
    related: EvidenceFile | None = None,
) -> None:
    db.add(
        Finding(
            analysis_run_id=run.id,
            evidence_file_id=evidence.id,
            related_evidence_file_id=related.id if related else None,
            category=category,
            severity=severity,
            rule_id=rule_id,
            rule_version=RULE_VERSION,
            title=title,
            explanation=explanation,
            supporting_data_json=json.dumps(support, default=str),
        )
    )


def run_analysis(db: Session, case_id: str, configuration: dict[str, object]) -> AnalysisRun:
    canonical = json.dumps(configuration, sort_keys=True, separators=(",", ":"))
    run = AnalysisRun(
        case_id=case_id,
        analyzer_version="1.0.0",
        rule_set_version=RULE_SET_VERSION,
        application_version=__version__,
        configuration_json=canonical,
        configuration_sha256=hashlib.sha256(canonical.encode()).hexdigest(),
        status="running",
    )
    db.add(run)
    db.flush()
    evidence = list(
        db.scalars(
            select(EvidenceFile)
            .where(EvidenceFile.case_id == case_id)
            .order_by(EvidenceFile.created_at)
        )
    )
    pattern_config = configuration.get("editor_patterns", [])
    patterns = (
        [str(value).lower() for value in pattern_config] if isinstance(pattern_config, list) else []
    )
    for item in evidence:
        meta = item.metadata_record
        if item.integrity_status == "mismatch":
            add_finding(
                db,
                run,
                item,
                "INTEGRITY_HASH_MISMATCH",
                "integrity",
                "high",
                "Integrity verification failed",
                "The current file hash does not match the acquisition hash.",
                {"acquisition_hash": item.sha256_acquisition, "current_hash": item.sha256_current},
            )
        if meta.timeline_timestamp_source == "filesystem_modified":
            add_finding(
                db,
                run,
                item,
                "TIMESTAMP_SOURCE_FALLBACK",
                "time",
                "info",
                "Timeline uses a fallback timestamp",
                "No higher-priority usable embedded timestamp was available.",
                {
                    "source": meta.timeline_timestamp_source,
                    "reason": meta.timestamp_selection_reason,
                },
            )
        timestamp_values = {
            "DateTimeOriginal": meta.datetime_original_raw,
            "DateTimeDigitized": meta.datetime_digitized_raw,
            "GPSDateTime": meta.gps_datetime_raw,
        }
        parsed_timestamps = {
            label: parsed.replace(tzinfo=None)
            for label, raw in timestamp_values.items()
            if raw and (parsed := parse_exif_datetime(raw)) is not None
        }
        discrepancy_config = configuration.get("timestamp_discrepancy_seconds", 300)
        discrepancy_threshold = (
            float(discrepancy_config)
            if isinstance(discrepancy_config, int | float | str)
            else 300.0
        )
        timestamp_pairs = [
            (left_label, right_label, abs((left - right).total_seconds()))
            for left_index, (left_label, left) in enumerate(parsed_timestamps.items())
            for right_label, right in list(parsed_timestamps.items())[left_index + 1 :]
        ]
        if timestamp_pairs:
            left_label, right_label, delta_seconds = max(timestamp_pairs, key=lambda pair: pair[2])
            if delta_seconds > discrepancy_threshold:
                add_finding(
                    db,
                    run,
                    item,
                    "TIMESTAMP_DISCREPANCY",
                    "time",
                    "review",
                    "Embedded timestamps differ beyond the configured threshold",
                    (
                        "Two reported timestamp fields differ in wall-clock time. Timezone context "
                        "may be incomplete, so qualified review is required."
                    ),
                    {
                        "fields": [left_label, right_label],
                        "values": [timestamp_values[left_label], timestamp_values[right_label]],
                        "difference_seconds": delta_seconds,
                        "threshold_seconds": discrepancy_threshold,
                    },
                )
        if meta.software and (
            matched := next((p for p in patterns if p in meta.software.lower()), None)
        ):
            add_finding(
                db,
                run,
                item,
                "EDITING_SOFTWARE_PRESENT",
                "metadata",
                "review",
                "Editing-software metadata present",
                (
                    "A configured editor pattern appears in the Software tag; "
                    "this does not establish manipulation."
                ),
                {"software_tag": meta.software, "matched_pattern": matched},
            )
        if meta.gps_latitude is None or meta.gps_longitude is None:
            add_finding(
                db,
                run,
                item,
                "MISSING_GPS",
                "location",
                "info",
                "No GPS metadata is available",
                "No usable coordinates were extracted from this image.",
                {"gps_available": False},
            )
    timed = [item for item in evidence if item.metadata_record.timeline_timestamp_utc is not None]
    timed.sort(
        key=lambda item: item.metadata_record.timeline_timestamp_utc
        or datetime.min.replace(tzinfo=UTC)
    )
    threshold_config = configuration.get("travel_speed_threshold_kmh", 1000)
    threshold = (
        float(threshold_config) if isinstance(threshold_config, int | float | str) else 1000.0
    )
    for previous, current in zip(timed, timed[1:], strict=False):
        pmeta, cmeta = previous.metadata_record, current.metadata_record
        if (
            pmeta.gps_latitude is not None
            and pmeta.gps_longitude is not None
            and cmeta.gps_latitude is not None
            and cmeta.gps_longitude is not None
            and pmeta.timeline_timezone_status != "local_unknown"
            and cmeta.timeline_timezone_status != "local_unknown"
        ):
            distance = haversine_km(
                pmeta.gps_latitude, pmeta.gps_longitude, cmeta.gps_latitude, cmeta.gps_longitude
            )
            interval = (
                (cmeta.timeline_timestamp_utc or datetime.now(UTC))
                - (pmeta.timeline_timestamp_utc or datetime.now(UTC))
            ).total_seconds()
            speed = speed_kmh(distance, interval)
            if speed is not None and speed > threshold:
                add_finding(
                    db,
                    run,
                    current,
                    "IMPLAUSIBLE_TRAVEL",
                    "location",
                    "review",
                    "Derived travel speed exceeds the configured threshold",
                    (
                        "This speed is derived from selected timestamps and coordinates, "
                        "not an observation of travel."
                    ),
                    {
                        "distance_km": round(distance, 3),
                        "interval_seconds": interval,
                        "derived_speed_kmh": round(speed, 3),
                        "threshold_kmh": threshold,
                        "timestamp_confidence": [
                            pmeta.timeline_timestamp_confidence,
                            cmeta.timeline_timestamp_confidence,
                        ],
                    },
                    previous,
                )
        if (pmeta.camera_make, pmeta.camera_model) != (cmeta.camera_make, cmeta.camera_model):
            add_finding(
                db,
                run,
                current,
                "CAMERA_SOURCE_CHANGE",
                "camera",
                "info",
                "Reported camera source changed",
                "Adjacent timeline items report different camera make/model groupings.",
                {
                    "previous": [pmeta.camera_make, pmeta.camera_model],
                    "current": [cmeta.camera_make, cmeta.camera_model],
                },
                previous,
            )
    run.status = "completed"
    run.completed_at = datetime.now(UTC)
    db.commit()
    return run
