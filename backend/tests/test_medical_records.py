from uuid import uuid4

from app.api.deps import get_current_user
from app.api.routes.medical_records import get_storage
from app.main import app
from app.models.user import User


class FakeStorage:
    def __init__(self, size=2048, content_type="application/pdf"):
        self.size = size
        self.content_type = content_type
        self.deleted = []

    def create_upload_url(self, key, content_type):
        return f"https://storage.example/upload/{key}"

    def head(self, key):
        return {"ContentLength": self.size, "ContentType": self.content_type}

    def delete(self, key):
        self.deleted.append(key)


def _user(role="patient"):
    return User(id=uuid4(), email=f"{uuid4()}@example.com", full_name="Test User", password_hash="unused", role=role, is_active=True)


def test_patient_can_create_and_list_medical_records(client):
    patient = _user()
    app.dependency_overrides[get_current_user] = lambda: patient
    created = client.post("/api/v1/medical-records", json={"title": "Blood Test", "category": "Lab", "content": "Hemoglobin: 13.5", "file_name": "blood-test.pdf", "mime_type": "application/pdf"})
    assert created.status_code == 201
    record = created.json()
    assert record["title"] == "Blood Test"
    assert record["category"] == "Lab"
    assert record["content"] == "Hemoglobin: 13.5"
    assert "storage_key" not in record
    listed = client.get("/api/v1/medical-records")
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == record["id"]


def test_patient_can_filter_medical_records_by_category(client):
    patient = _user()
    app.dependency_overrides[get_current_user] = lambda: patient
    for category in ["Lab", "Prescription"]:
        assert client.post("/api/v1/medical-records", json={"title": category, "category": category}).status_code == 201
    response = client.get("/api/v1/medical-records", params={"category": "Lab"})
    assert response.status_code == 200
    assert [item["category"] for item in response.json()] == ["Lab"]


def test_patient_cannot_read_another_patients_record(client):
    first_patient = _user()
    app.dependency_overrides[get_current_user] = lambda: first_patient
    record_id = client.post("/api/v1/medical-records", json={"title": "Private Record", "category": "Doctor note"}).json()["id"]
    second_patient = _user()
    app.dependency_overrides[get_current_user] = lambda: second_patient
    assert client.get(f"/api/v1/medical-records/{record_id}").status_code == 404
    assert client.get("/api/v1/medical-records").json() == []


def test_doctor_cannot_access_patient_record_without_explicit_access(client):
    patient = _user()
    app.dependency_overrides[get_current_user] = lambda: patient
    record_id = client.post("/api/v1/medical-records", json={"title": "Sensitive Record", "category": "Allergy"}).json()["id"]
    doctor = _user("doctor")
    app.dependency_overrides[get_current_user] = lambda: doctor
    assert client.get(f"/api/v1/medical-records/{record_id}").status_code == 404
    assert client.get("/api/v1/medical-records").json() == []


def test_patient_gets_presigned_medical_record_upload_url(client):
    patient = _user()
    storage = FakeStorage()
    app.dependency_overrides[get_current_user] = lambda: patient
    app.dependency_overrides[get_storage] = lambda: storage
    response = client.post("/api/v1/medical-records/upload-url", json={"title": "Scan", "category": "Lab", "file_name": "scan.pdf", "mime_type": "application/pdf"})
    assert response.status_code == 201
    body = response.json()
    assert body["upload_url"].startswith("https://storage.example/upload/")
    assert body["storage_key"].startswith(f"medical-records/{patient.id}/")
    record = client.get(f"/api/v1/medical-records/{body['record_id']}").json()
    assert record["file_name"] == "scan.pdf"
    assert record["upload_completed_at"] is None


def test_upload_rejects_unsupported_file_type(client):
    patient = _user()
    app.dependency_overrides[get_current_user] = lambda: patient
    app.dependency_overrides[get_storage] = lambda: FakeStorage()
    response = client.post("/api/v1/medical-records/upload-url", json={"title": "Script", "category": "Lab", "file_name": "report.exe", "mime_type": "application/octet-stream"})
    assert response.status_code == 415


def test_patient_can_complete_upload_and_record_is_finalized(client):
    patient = _user()
    storage = FakeStorage()
    app.dependency_overrides[get_current_user] = lambda: patient
    app.dependency_overrides[get_storage] = lambda: storage
    created = client.post("/api/v1/medical-records/upload-url", json={"title": "Scan", "category": "Lab", "file_name": "scan.pdf", "mime_type": "application/pdf"}).json()
    completed = client.post(f"/api/v1/medical-records/{created['record_id']}/complete", json={})
    assert completed.status_code == 200
    body = completed.json()
    assert body["file_size"] == 2048
    assert body["upload_completed_at"] is not None


def test_upload_completion_enforces_patient_ownership(client):
    patient = _user()
    app.dependency_overrides[get_current_user] = lambda: patient
    app.dependency_overrides[get_storage] = lambda: FakeStorage()
    created = client.post("/api/v1/medical-records/upload-url", json={"title": "Private", "category": "Lab", "file_name": "scan.pdf", "mime_type": "application/pdf"}).json()
    other_patient = _user()
    app.dependency_overrides[get_current_user] = lambda: other_patient
    assert client.post(f"/api/v1/medical-records/{created['record_id']}/complete", json={}).status_code == 404
