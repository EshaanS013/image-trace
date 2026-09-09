from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


@dataclass(frozen=True)
class TimestampSelection:
    raw: str
    normalized_utc: datetime | None
    source: str
    timezone_status: str
    confidence: str
    reason: str


def parse_exif_datetime(value: str) -> datetime | None:
    for pattern in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S%z"):
        try:
            return datetime.strptime(value, pattern)
        except ValueError:
            continue
    return None


def select_timestamp(
    original: str | None,
    digitized: str | None,
    gps: str | None,
    filesystem_modified: datetime,
    case_timezone: str | None = None,
) -> TimestampSelection:
    candidates = [
        ("datetime_original", original, "high"),
        ("datetime_digitized", digitized, "medium"),
        ("gps_datetime", gps, "high"),
    ]
    rejected: list[str] = []
    for source, raw, confidence in candidates:
        if not raw:
            rejected.append(f"{source} unavailable")
            continue
        parsed = parse_exif_datetime(raw)
        if parsed is None:
            rejected.append(f"{source} malformed")
            continue
        if parsed.tzinfo:
            return TimestampSelection(
                raw,
                parsed.astimezone(UTC),
                source,
                "known",
                confidence,
                "; ".join(rejected) or "highest-priority usable source",
            )
        if case_timezone:
            try:
                assumed = parsed.replace(tzinfo=ZoneInfo(case_timezone)).astimezone(UTC)
                return TimestampSelection(
                    raw,
                    assumed,
                    source,
                    "case_assumption",
                    confidence,
                    f"Case timezone assumption: {case_timezone}",
                )
            except ZoneInfoNotFoundError:
                rejected.append("case timezone invalid")
        return TimestampSelection(
            raw,
            None,
            source,
            "local_unknown",
            confidence,
            "Timezone-naive capture timestamp preserved without UTC conversion",
        )
    fallback = filesystem_modified.astimezone(UTC)
    return TimestampSelection(
        fallback.isoformat(), fallback, "filesystem_modified", "known", "low", "; ".join(rejected)
    )
