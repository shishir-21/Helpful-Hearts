from uuid import uuid4

from app.api.deps import get_current_user
from app.main import app
from app.models.user import User


def _user(role="patient"):
    return User(
        id=uuid4(),
        email=f"{uuid4()}@example.com",
        full_name="Test User",
        password_hash="unused",
        role=role,
        is_active=True,
    )


def test_patient_can_create_and_list_medical_records(client):
    patient = _user()
    app.dependency_overrides[get_current_user] = lambda: patient

    created = client.post(
        "/api/v1/medical-records",
        json={
            "title": "Blood Test",
            "category": "Lab",
            "content": "Hemoglobin: 13.5",
            "file_name": "blood-test.pdf",
            "mime_type": "application/pdf",
        },
    )
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
        response = client.post(
            "/api/v1/medical-records",
            json={"title": category, "category": category},
        )
        assert response.status_code == 201

    response = client.get("/api/v1/medical-records", params={"category": "Lab"})
    assert response.status_code == 200
    assert [item["category"] for item in response.json()] == ["Lab"]


def test_patient_cannot_read_another_patients_record(client):
    first_patient = _user()
    app.dependency_overrides[get_current_user] = lambda: first_patient

    created = client.post(
        "/api/v1/medical-records",
        json={"title": "Private Record", "category": "Doctor note"},
    )
    assert created.status_code == 201
    record_id = created.json()["id"]

    second_patient = _user()
    app.dependency_overrides[get_current_user] = lambda: second_patient

    assert client.get(f"/api/v1/medical-records/{record_id}").status_code == 404
    assert client.get("/api/v1/medical-records").json() == []


def test_doctor_cannot_access_patient_record_without_explicit_access(client):
    patient = _user()
    app.dependency_overrides[get_current_user] = lambda: patient
    created = client.post(
        "/api/v1/medical-records",
        json={"title": "Sensitive Record", "category": "Allergy"},
    )
    record_id = created.json()["id"]

    doctor = _user("doctor")
    app.dependency_overrides[get_current_user] = lambda: doctor

    assert client.get(f"/api/v1/medical-records/{record_id}").status_code == 404
    assert client.get("/api/v1/medical-records").json() == []
