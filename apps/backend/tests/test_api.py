import io

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session

from image_trace.models import EvidenceFile
from image_trace.services.storage_service import storage


def image_bytes(fmt: str = "PNG") -> bytes:
    stream = io.BytesIO()
    Image.new("RGB", (32, 24), "navy").save(stream, fmt)
    return stream.getvalue()


def create_case(client: TestClient) -> str:
    response = client.post(
        "/api/v1/cases",
        json={
            "case_number": "CASE-001",
            "name": "Synthetic review",
            "description": "Consented fixture",
            "analyst_name": "Test Analyst",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_case_upload_analysis_review_report_and_manifest(client: TestClient) -> None:
    case_id = create_case(client)
    upload = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        data={"acquired_by": "Test Analyst"},
        files=[("files", ("frame.png", image_bytes(), "image/png"))],
    )
    assert upload.status_code == 201 and len(upload.json()["accepted"]) == 1
    evidence = upload.json()["accepted"][0]
    assert evidence["sha256_acquisition"] == evidence["sha256_current"]
    analysis = client.post(f"/api/v1/cases/{case_id}/analysis-runs", json={})
    assert analysis.status_code == 201 and analysis.json()["status"] == "completed"
    findings = client.get(f"/api/v1/cases/{case_id}/findings").json()
    assert {item["rule_id"] for item in findings} >= {"TIMESTAMP_SOURCE_FALLBACK", "MISSING_GPS"}
    changed = client.patch(
        f"/api/v1/findings/{findings[0]['id']}",
        json={
            "reviewer_status": "acknowledged",
            "disposition": "Reviewed context",
            "actor": "Test Analyst",
            "note": "Expected for this fixture",
        },
    )
    assert changed.status_code == 200 and changed.json()["reviewer_status"] == "acknowledged"
    report = client.post(
        f"/api/v1/cases/{case_id}/reports",
        json={
            "analysis_run_id": analysis.json()["id"],
            "generated_by": "Test Analyst",
            "redact_coordinates": True,
        },
    )
    assert report.status_code == 201
    assert client.get(f"/api/v1/reports/{report.json()['id']}/download").content.startswith(b"%PDF")
    manifest = client.get(f"/api/v1/reports/{report.json()['id']}/manifest").text
    assert report.json()["sha256"] in manifest and analysis.json()["id"] in manifest


def test_validation_and_controlled_integrity_mismatch(client: TestClient, db: Session) -> None:
    case_id = create_case(client)
    bad = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        data={"acquired_by": "Test Analyst"},
        files=[
            ("files", ("../escape.png", image_bytes(), "image/png")),
            ("files", ("not-image.png", b"not an image", "image/png")),
            ("files", ("wrong.jpg", image_bytes(), "image/jpeg")),
        ],
    )
    assert bad.status_code == 201 and len(bad.json()["failures"]) == 3
    good = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        data={"acquired_by": "Test Analyst"},
        files=[("files", ("valid.png", image_bytes(), "image/png"))],
    ).json()["accepted"][0]
    item = db.get(EvidenceFile, good["id"])
    assert item is not None
    path = storage.resolve(item.storage_key)
    path.write_bytes(path.read_bytes() + b"controlled-test-mutation")
    verified = client.post(f"/api/v1/evidence/{item.id}/verify-integrity?actor=Test%20Analyst")
    assert verified.json()["integrity_status"] == "mismatch"
    events = client.get(f"/api/v1/cases/{case_id}/custody-events").json()
    assert any(event["event_type"] == "integrity_verified" for event in events)
