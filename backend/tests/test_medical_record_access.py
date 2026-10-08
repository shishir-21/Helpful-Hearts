from uuid import uuid4

from app.api.deps import get_current_user
from app.main import app
from app.models.doctor import Doctor
from app.models.user import User


def user(role="patient"):
    return User(id=uuid4(), email=f"{uuid4()}@example.com", full_name="Test User", password_hash="unused", role=role, is_active=True)


def doctor_profile(db, doctor_user):
    doctor = Doctor(id=uuid4(), user_id=doctor_user.id, full_name="Dr Test", specialty="General Medicine")
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


def test_patient_can_grant_and_revoke_doctor_record_access(client, db_session):
    patient = user()
    doctor_user = user("doctor")
    doctor = doctor_profile(db_session, doctor_user)
    app.dependency_overrides[get_current_user] = lambda: patient

    record = client.post("/api/v1/medical-records", json={"title": "Lab", "category": "Lab"}).json()
    grant = client.post(f"/api/v1/medical-records/{record['id']}/access", json={"doctor_id": str(doctor.id)})
    assert grant.status_code == 201
    assert grant.json()["doctor_id"] == str(doctor.id)

    duplicate = client.post(f"/api/v1/medical-records/{record['id']}/access", json={"doctor_id": str(doctor.id)})
    assert duplicate.status_code == 409

    revoked = client.delete(f"/api/v1/medical-records/{record['id']}/access/{doctor.id}")
    assert revoked.status_code == 204


def test_doctor_sees_only_explicitly_shared_records(client, db_session):
    patient = user()
    doctor_user = user("doctor")
    doctor = doctor_profile(db_session, doctor_user)
    app.dependency_overrides[get_current_user] = lambda: patient

    shared = client.post("/api/v1/medical-records", json={"title": "Shared", "category": "Lab"}).json()
    private = client.post("/api/v1/medical-records", json={"title": "Private", "category": "Allergy"}).json()
    assert client.post(f"/api/v1/medical-records/{shared['id']}/access", json={"doctor_id": str(doctor.id)}).status_code == 201

    from app.api.deps import get_current_doctor
    app.dependency_overrides[get_current_doctor] = lambda: doctor

    listed = client.get("/api/v1/medical-records/shared-with-me")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [shared["id"]]
    assert client.get(f"/api/v1/medical-records/{shared['id']}/shared").status_code == 200
    assert client.get(f"/api/v1/medical-records/{private['id']}/shared").status_code == 404
