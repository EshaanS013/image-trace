import json
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

from PIL import ExifTags, Image

from ..models import ImageMetadata
from .geo_service import dms_to_decimal
from .timeline_service import select_timestamp


def safe_value(value: Any) -> Any:
    if isinstance(value, bytes):
        return value[:256].hex()
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    if isinstance(value, tuple | list):
        return [safe_value(item) for item in value[:100]]
    if isinstance(value, dict):
        return {str(key)[:100]: safe_value(item) for key, item in list(value.items())[:200]}
    return str(value)[:1000]


def ratio(value: Any) -> float:
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        return float(Fraction(value.numerator, value.denominator))
    return float(value)


def gps_decimal(gps: dict[str, Any], coordinate: str, reference: str) -> float | None:
    values, ref = gps.get(coordinate), gps.get(reference)
    if not values or not ref or len(values) != 3:
        return None
    return dms_to_decimal(ratio(values[0]), ratio(values[1]), ratio(values[2]), str(ref))


def extract_metadata(
    path: Path, modified_at: datetime, case_timezone: str | None = None
) -> ImageMetadata:
    warnings: list[str] = []
    with Image.open(path) as image:
        exif = image.getexif()
        named: dict[str, Any] = {}
        for key, value in exif.items():
            name = ExifTags.TAGS.get(key, str(key))
            named[name] = safe_value(value)
        gps_raw = exif.get_ifd(ExifTags.IFD.GPSInfo) if hasattr(ExifTags, "IFD") and exif else {}
        gps = {ExifTags.GPSTAGS.get(key, str(key)): value for key, value in gps_raw.items()}
        try:
            latitude = gps_decimal(gps, "GPSLatitude", "GPSLatitudeRef")
            longitude = gps_decimal(gps, "GPSLongitude", "GPSLongitudeRef")
        except (TypeError, ValueError, ZeroDivisionError) as error:
            latitude = longitude = None
            warnings.append(f"GPS normalization skipped: {error}")
        gps_datetime = None
        if gps.get("GPSDateStamp") and gps.get("GPSTimeStamp"):
            try:
                hh, mm, ss = (int(ratio(item)) for item in gps["GPSTimeStamp"])
                gps_datetime = f"{gps['GPSDateStamp']} {hh:02}:{mm:02}:{ss:02}+0000"
            except (TypeError, ValueError, ZeroDivisionError):
                warnings.append("GPS date/time could not be normalized")
        selected = select_timestamp(
            named.get("DateTimeOriginal"),
            named.get("DateTimeDigitized"),
            gps_datetime,
            modified_at,
            case_timezone,
        )
        return ImageMetadata(
            raw_metadata_json=json.dumps(
                {"exif": named, "gps": safe_value(gps)}, ensure_ascii=False
            ),
            datetime_original_raw=named.get("DateTimeOriginal"),
            datetime_digitized_raw=named.get("DateTimeDigitized"),
            gps_datetime_raw=gps_datetime,
            timeline_timestamp_raw=selected.raw,
            timeline_timestamp_utc=selected.normalized_utc,
            timeline_timezone_status=selected.timezone_status,
            timeline_timestamp_source=selected.source,
            timeline_timestamp_confidence=selected.confidence,
            timestamp_selection_reason=selected.reason,
            gps_latitude=latitude,
            gps_longitude=longitude,
            gps_altitude=ratio(gps["GPSAltitude"]) if gps.get("GPSAltitude") else None,
            camera_make=str(named.get("Make"))[:160] if named.get("Make") else None,
            camera_model=str(named.get("Model"))[:160] if named.get("Model") else None,
            lens_model=str(named.get("LensModel"))[:160] if named.get("LensModel") else None,
            camera_serial_number=str(named.get("BodySerialNumber"))[:160]
            if named.get("BodySerialNumber")
            else None,
            focal_length=str(named.get("FocalLength"))[:80] if named.get("FocalLength") else None,
            iso=str(named.get("ISOSpeedRatings"))[:80] if named.get("ISOSpeedRatings") else None,
            aperture=str(named.get("FNumber"))[:80] if named.get("FNumber") else None,
            shutter_speed=str(named.get("ExposureTime"))[:80]
            if named.get("ExposureTime")
            else None,
            software=str(named.get("Software"))[:200] if named.get("Software") else None,
            width=image.width,
            height=image.height,
            orientation=str(named.get("Orientation"))[:80] if named.get("Orientation") else None,
            extraction_warnings_json=json.dumps(warnings),
        )
