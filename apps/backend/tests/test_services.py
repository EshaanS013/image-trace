import io
from datetime import UTC, datetime
from pathlib import Path

from image_trace.services.geo_service import dms_to_decimal, haversine_km, speed_kmh
from image_trace.services.hash_service import hash_file, hash_stream
from image_trace.services.timeline_service import select_timestamp


def test_chunked_hash_empty_and_large(tmp_path: Path) -> None:
    digest, size = hash_stream(io.BytesIO(b""))
    assert digest == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert size == 0
    path = tmp_path / "large.bin"
    path.write_bytes(b"trace" * 500_000)
    assert hash_file(path) == hash_stream(io.BytesIO(path.read_bytes()))[0]


def test_geo_math() -> None:
    assert dms_to_decimal(12, 30, 0, "S") == -12.5
    assert round(haversine_km(0, 0, 0, 1), 1) == 111.2
    assert speed_kmh(100, 3600) == 100
    assert speed_kmh(100, 0) is None


def test_timestamp_priority_and_naive_policy() -> None:
    fallback = datetime(2026, 1, 1, tzinfo=UTC)
    naive = select_timestamp("2026:02:03 04:05:06", None, None, fallback)
    assert naive.source == "datetime_original" and naive.normalized_utc is None
    assert naive.timezone_status == "local_unknown"
    assumed = select_timestamp("2026:02:03 04:05:06", None, None, fallback, "Asia/Kolkata")
    assert assumed.normalized_utc is not None and assumed.timezone_status == "case_assumption"
    selected = select_timestamp(None, "2026:02:03 04:05:06", None, fallback)
    assert selected.source == "datetime_digitized"
    fallback_selected = select_timestamp(None, None, None, fallback)
    assert (
        fallback_selected.source == "filesystem_modified" and fallback_selected.confidence == "low"
    )
