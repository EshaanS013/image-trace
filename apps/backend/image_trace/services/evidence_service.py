import json
import os
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path, PurePath
from typing import BinaryIO

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Case, CustodyEvent, EvidenceFile
from .hash_service import hash_file
from .metadata_service import extract_metadata
from .storage_service import storage

Image.MAX_IMAGE_PIXELS = settings.max_megapixels * 1_000_000
ALLOWED_FORMATS = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
    "TIFF": "image/tiff",
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


class EvidenceError(ValueError):
    pass


def validate_filename(filename: str) -> None:
    if not filename or PurePath(filename).name != filename or filename in {".", ".."}:
        raise EvidenceError("Filename is missing or contains a path")
    if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise EvidenceError("Unsupported image extension")


def preserve_upload(stream: BinaryIO, destination: Path, max_bytes: int) -> int:
    destination.parent.mkdir(parents=True, exist_ok=False)
    temp = destination.with_suffix(".pending")
    size = 0
    try:
        with temp.open("xb") as output:
            while chunk := stream.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    raise EvidenceError(f"File exceeds the {settings.max_file_mib} MiB limit")
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        temp.replace(destination)
    except Exception:
        temp.unlink(missing_ok=True)
        if destination.parent.exists():
            shutil.rmtree(destination.parent)
        raise
    return size


def register_upload(db: Session, case: Case, upload: UploadFile, actor: str) -> EvidenceFile:
    filename = upload.filename or ""
    validate_filename(filename)
    generated_id = str(uuid.uuid4())
    storage_key, destination = storage.original_path(case.id, generated_id)
    try:
        size = preserve_upload(upload.file, destination, settings.max_file_mib * 1024 * 1024)
        try:
            with Image.open(destination) as image:
                image.verify()
            with Image.open(destination) as image:
                image.load()
                detected_format = image.format
                width, height = image.size
        except (UnidentifiedImageError, OSError, SyntaxError) as error:
            raise EvidenceError("File content is not a decodable supported image") from error
        if detected_format not in ALLOWED_FORMATS:
            raise EvidenceError("Decoded image format is not supported")
        expected_mime = ALLOWED_FORMATS[detected_format]
        if upload.content_type and upload.content_type not in {
            expected_mime,
            "application/octet-stream",
        }:
            raise EvidenceError("Declared MIME type does not match decoded image content")
        extension_family = Path(filename).suffix.lower()
        compatible = {"JPEG": {".jpg", ".jpeg"}, "TIFF": {".tif", ".tiff"}}.get(
            detected_format, {f".{detected_format.lower()}"}
        )
        if extension_family not in compatible:
            raise EvidenceError("Filename extension does not match decoded image content")
        if width * height > settings.max_megapixels * 1_000_000:
            raise EvidenceError(f"Image exceeds the {settings.max_megapixels} megapixel limit")
        digest = hash_file(destination)
        sequence = (
            db.scalar(
                select(func.count())
                .select_from(EvidenceFile)
                .where(EvidenceFile.case_id == case.id)
            )
            or 0
        )
        evidence = EvidenceFile(
            id=generated_id,
            case_id=case.id,
            evidence_id=f"IMG-{sequence + 1:04d}",
            original_filename=filename,
            storage_key=storage_key,
            mime_type=expected_mime,
            file_size=size,
            width=width,
            height=height,
            acquired_by=actor,
            sha256_acquisition=digest,
            sha256_current=digest,
            integrity_status="verified",
        )
        modified = datetime.fromtimestamp(destination.stat().st_mtime, tz=UTC)
        metadata = extract_metadata(destination, modified, case.case_timezone)
        evidence.metadata_record = metadata
        db.add(evidence)
        db.add(
            CustodyEvent(
                case_id=case.id,
                evidence_file_id=evidence.id,
                event_type="acquired",
                actor=actor,
                details_json=json.dumps(
                    {"sha256": digest, "original_filename": filename, "size": size}
                ),
            )
        )
        db.commit()
        create_thumbnail(destination, case.id, generated_id)
        return evidence
    except Exception:
        db.rollback()
        if destination.parent.exists():
            shutil.rmtree(destination.parent)
        raise


def create_thumbnail(source: Path, case_id: str, evidence_id: str) -> Path:
    _, target = storage.thumbnail_path(case_id, evidence_id)
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image.thumbnail((640, 640))
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGB")
        image.save(target, "WEBP", quality=82, method=6)
    return target


def verify_integrity(db: Session, evidence: EvidenceFile, actor: str) -> EvidenceFile:
    current = hash_file(storage.resolve(evidence.storage_key))
    evidence.sha256_current = current
    evidence.integrity_status = "verified" if current == evidence.sha256_acquisition else "mismatch"
    db.add(
        CustodyEvent(
            case_id=evidence.case_id,
            evidence_file_id=evidence.id,
            event_type="integrity_verified",
            actor=actor,
            details_json=json.dumps(
                {
                    "acquisition_hash": evidence.sha256_acquisition,
                    "current_hash": current,
                    "status": evidence.integrity_status,
                }
            ),
        )
    )
    db.commit()
    return evidence
