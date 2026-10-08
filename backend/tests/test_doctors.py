from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_doctor, get_current_user, get_db, require_roles
from app.db.session import Base
from app.main import app
from app.models.doctor import Doctor
from app.models.user import User


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        test_client.testing_session = testing_session
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _user(role: str) -> User:
    return User(
        id=uuid4(),
        email=f"{role}-{uuid4()}@example.com",
        full_name=f"Test {role}",
        password_hash="not-used",
        role=role,
        is_active=True,
    )


def test_admin_can_create_doctor_and_credentials(client):
    app.dependency_overrides[get_current_user] = lambda: _user("admin")

    doctor_response = client.post(
        "/api/v1/admin/doctors",
        json={
            "full_name": "Dr. Example Person",
            "specialty": "General Medicine",
            "hospital_name": "Example Clinic",
            "is_demo": True,
            "source_name": "Fictional test data",
        },
    )
    assert doctor_response.status_code == 201
    doctor = doctor_response.json()
    doctor_id = doctor["id"]
    assert doctor["profile_status"] == "draft"
    assert doctor["hospital_name"] == "Example Clinic"
    assert doctor["credentials"] == []

    credential_response = client.post(
        f"/api/v1/admin/doctors/{doctor_id}/credentials",
        json={
            "degree": "MBBS (Demo)",
            "institution": "Fictional Medical College",
            "verification_status": "unverified",
            "source_name": "Fictional test data",
        },
    )
    assert credential_response.status_code == 201
    assert credential_response.json()["credentials"][0]["degree"] == "MBBS (Demo)"


def test_admin_routes_reject_patient(client):
    app.dependency_overrides[get_current_user] = lambda: _user("patient")
    response = client.get("/api/v1/admin/doctors")
    assert response.status_code == 403


def test_admin_routes_reject_anonymous_user(client):
    response = client.get("/api/v1/admin/doctors")
    assert response.status_code == 401


def test_hospital_management_routes_are_not_exposed(client):
    app.dependency_overrides[get_current_user] = lambda: _user("admin")
    assert client.get("/api/v1/admin/hospitals").status_code == 404
    assert client.post("/api/v1/admin/hospitals", json={}).status_code == 404


def test_public_search_and_profile_only_return_verified_doctors(client):
    app.dependency_overrides[get_current_user] = lambda: _user("admin")
    response = client.post(
        "/api/v1/admin/doctors",
        json={
            "full_name": "Dr. Verified Example",
            "specialty": "Cardiology",
            "hospital_name": "Example Clinic",
            "profile_status": "verified",
            "is_demo": True,
            "source_name": "Fictional test data",
        },
    )
    assert response.status_code == 201
    doctor_id = response.json()["id"]

    public_list = client.get("/api/v1/doctors?q=Verified&specialty=Cardiology&page=1&page_size=5")
    assert public_list.status_code == 200
    payload = public_list.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == doctor_id

    public_profile = client.get(f"/api/v1/doctors/{doctor_id}")
    assert public_profile.status_code == 200
    assert public_profile.json()["full_name"] == "Dr. Verified Example"
    assert "registration_number" not in public_profile.json()
    assert "verification_note" not in public_profile.json()


def test_public_search_hides_draft_profiles(client):
    app.dependency_overrides[get_current_user] = lambda: _user("admin")
    response = client.post(
        "/api/v1/admin/doctors",
        json={
            "full_name": "Dr. Draft Example",
            "specialty": "General Medicine",
            "profile_status": "draft",
            "is_demo": True,
            "source_name": "Fictional test data",
        },
    )
    assert response.status_code == 201
    doctor_id = response.json()["id"]
    assert client.get(f"/api/v1/doctors/{doctor_id}").status_code == 404
    assert client.get("/api/v1/doctors?q=Draft").json()["total"] == 0


def test_admin_can_link_doctor_profile_to_doctor_user(client):
    app.dependency_overrides[get_current_user] = lambda: _user("admin")
    doctor_response = client.post(
        "/api/v1/admin/doctors",
        json={
            "full_name": "Dr. Linked Example",
            "specialty": "Cardiology",
            "is_demo": True,
            "source_name": "Fictional test data",
        },
    )
    assert doctor_response.status_code == 201
    doctor_id = doctor_response.json()["id"]

    doctor_user = _user("doctor")
    db = client.testing_session()
    db.add(doctor_user)
    db.commit()

    response = client.patch(
        f"/api/v1/admin/doctors/{doctor_id}/user-link",
        json={"user_id": str(doctor_user.id)},
    )
    assert response.status_code == 200
    assert response.json()["user_id"] == str(doctor_user.id)

    duplicate_doctor = client.post(
        "/api/v1/admin/doctors",
        json={
            "full_name": "Dr. Duplicate Link",
            "specialty": "Dermatology",
            "is_demo": True,
            "source_name": "Fictional test data",
        },
    )
    assert duplicate_doctor.status_code == 201

    duplicate_response = client.patch(
        f"/api/v1/admin/doctors/{duplicate_doctor.json()['id']}/user-link",
        json={"user_id": str(doctor_user.id)},
    )
    assert duplicate_response.status_code == 409


def test_admin_cannot_link_non_doctor_user(client):
    app.dependency_overrides[get_current_user] = lambda: _user("admin")
    doctor_response = client.post(
        "/api/v1/admin/doctors",
        json={
            "full_name": "Dr. Link Validation",
            "specialty": "Neurology",
            "is_demo": True,
            "source_name": "Fictional test data",
        },
    )
    assert doctor_response.status_code == 201

    patient = _user("patient")
    db = client.testing_session()
    db.add(patient)
    db.commit()

    response = client.patch(
        f"/api/v1/admin/doctors/{doctor_response.json()['id']}/user-link",
        json={"user_id": str(patient.id)},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Linked user must have the doctor role"


def test_doctor_identity_resolves_only_its_linked_profile(client):
    doctor_user = _user("doctor")
    other_doctor_user = _user("doctor")
    db = client.testing_session()
    db.add_all([doctor_user, other_doctor_user])
    db.flush()

    own_doctor = Doctor(
        user_id=doctor_user.id,
        full_name="Dr. Own Profile",
        specialty="Cardiology",
        source_name="Fictional test data",
    )
    other_doctor = Doctor(
        user_id=other_doctor_user.id,
        full_name="Dr. Other Profile",
        specialty="Neurology",
        source_name="Fictional test data",
    )
    db.add_all([own_doctor, other_doctor])
    db.commit()

    resolved = get_current_doctor(current_user=doctor_user, db=db)
    assert resolved.id == own_doctor.id
    assert resolved.id != other_doctor.id


def test_doctor_role_guard_rejects_patient():
    patient = _user("patient")
    doctor_only = require_roles("doctor")
    with pytest.raises(Exception) as exc_info:
        doctor_only(patient)
    assert exc_info.value.status_code == 403


def test_doctor_without_profile_link_gets_not_found(client):
    doctor_user = _user("doctor")
    db = client.testing_session()
    db.add(doctor_user)
    db.commit()

    with pytest.raises(Exception) as exc_info:
        get_current_doctor(current_user=doctor_user, db=db)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Doctor profile not linked"
