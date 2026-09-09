"""Generate a deterministic, public-safe synthetic IMAGE TRACE case."""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

import piexif
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "fixtures" / "synthetic-case"
GENERATOR_VERSION = "1.0.0"


def rational(value: float) -> tuple[int, int]:
    return int(round(value * 10_000)), 10_000


def gps_dms(value: float) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    absolute = abs(value)
    degrees = int(absolute)
    minutes_float = (absolute - degrees) * 60
    minutes = int(minutes_float)
    seconds = (minutes_float - minutes) * 60
    return (degrees, 1), (minutes, 1), rational(seconds)


def exif_bytes(index: int, timestamp: datetime, lat: float | None, lon: float | None) -> bytes:
    camera = ("TraceCam", "TC-100") if index < 10 else ("FieldOptics", "FO-2")
    digitized = timestamp + timedelta(hours=2) if index == 5 else timestamp
    exif = {
        "0th": {piexif.ImageIFD.Make: camera[0], piexif.ImageIFD.Model: camera[1], piexif.ImageIFD.Software: "Adobe Photoshop synthetic example" if index == 4 else "IMAGE TRACE Fixture Generator"},
        "Exif": {piexif.ExifIFD.DateTimeOriginal: timestamp.strftime("%Y:%m:%d %H:%M:%S"), piexif.ExifIFD.DateTimeDigitized: digitized.strftime("%Y:%m:%d %H:%M:%S"), piexif.ExifIFD.LensModel: "Synthetic 35mm", piexif.ExifIFD.ISOSpeedRatings: 100 + index},
        "GPS": {}, "1st": {}, "thumbnail": None,
    }
    if index == 7:
        exif["Exif"].pop(piexif.ExifIFD.DateTimeOriginal)
    if lat is not None and lon is not None:
        exif["GPS"] = {piexif.GPSIFD.GPSLatitudeRef: b"N" if lat >= 0 else b"S", piexif.GPSIFD.GPSLatitude: gps_dms(lat),
                       piexif.GPSIFD.GPSLongitudeRef: b"E" if lon >= 0 else b"W", piexif.GPSIFD.GPSLongitude: gps_dms(lon),
                       piexif.GPSIFD.GPSDateStamp: timestamp.strftime("%Y:%m:%d"),
                       piexif.GPSIFD.GPSTimeStamp: ((timestamp.hour, 1), (timestamp.minute, 1), (timestamp.second, 1))}
    return piexif.dump(exif)


def generate() -> None:
    TARGET.mkdir(parents=True, exist_ok=True)
    for old in TARGET.glob("synthetic-*.jpg"):
        old.unlink()
    start = datetime(2026, 1, 15, 8, 0, tzinfo=timezone.utc)
    entries = []
    coords: list[tuple[float, float] | None] = [(12.9716 + i * 0.005, 77.5946 + i * 0.004) for i in range(13)] + [None] * 7
    coords[10] = (51.5074, -0.1278)
    for index in range(20):
        name = f"synthetic-{index + 1:02d}.jpg"
        path = TARGET / name
        timestamp = start + timedelta(minutes=index * 15)
        location = coords[index]
        image = Image.new("RGB", (640, 420), ((31 + index * 7) % 255, (82 + index * 11) % 255, (123 + index * 13) % 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle((28, 28, 612, 392), outline="white", width=4)
        draw.text((52, 54), f"SYNTHETIC EVIDENCE {index + 1:02d}", fill="white")
        draw.text((52, 340), "No person or real location is depicted", fill="white")
        image.save(path, "JPEG", quality=91, exif=exif_bytes(index, timestamp, *(location or (None, None))))
        entries.append({"filename": name, "camera_group": "A" if index < 10 else "B", "gps_expected": location is not None,
                        "timestamp": timestamp.isoformat(), "editing_software_example": index == 4})
    shutil.copyfile(TARGET / "synthetic-02.jpg", TARGET / "synthetic-19.jpg")
    near = Image.open(TARGET / "synthetic-03.jpg"); pixels = near.load(); pixels[0, 0] = (pixels[0, 0][0] ^ 1, pixels[0, 0][1], pixels[0, 0][2]); near.save(TARGET / "synthetic-20.jpg", "JPEG", quality=91)
    entries[18].update(entries[1] | {"filename": "synthetic-19.jpg", "exact_duplicate_of": "synthetic-02.jpg"})
    entries[19].update({"camera_group": None, "gps_expected": False, "timestamp": None, "near_duplicate_of": "synthetic-03.jpg"})
    for entry in entries:
        content = (TARGET / entry["filename"]).read_bytes()
        entry["sha256"] = hashlib.sha256(content).hexdigest()
    manifest = {"generator_version": GENERATOR_VERSION, "synthetic_only": True, "coordinate_policy": "Synthetic coordinates for testing; not tied to depicted people or events.",
                "expected": {"image_count": 20, "gps_count": 14, "camera_groups": 2, "editing_software_examples": 1,
                             "implausible_transition": ["synthetic-10.jpg", "synthetic-11.jpg"], "exact_duplicate": ["synthetic-02.jpg", "synthetic-19.jpg"],
                             "near_duplicate": ["synthetic-03.jpg", "synthetic-20.jpg"], "timestamp_discrepancy": "synthetic-06.jpg", "minimum_finding_rules": ["TIMESTAMP_SOURCE_FALLBACK", "TIMESTAMP_DISCREPANCY", "EDITING_SOFTWARE_PRESENT", "IMPLAUSIBLE_TRAVEL", "MISSING_GPS", "CAMERA_SOURCE_CHANGE"]},
                "files": entries}
    (TARGET / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    generate()
