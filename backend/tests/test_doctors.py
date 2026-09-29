from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user, get_db
from app.db.session import Base
from app.main import app
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


def test_admin_can_create_hospital_doctor_and_affiliation(client):
    admin = _user("admin")
    app.dependency_overrides[get_current_user] = lambda: admin

    hospital_response = client.post(
        "/api/v1/admin/hospitals",
        json={
            "name": "Demo Hospital",
            "address": "1 Example Street",
            "city": "Demo City",
            "is_demo": True,
            "source_name": "Fictional test data",
        },
    )
    assert hospital_response.status_code == 201
    hospital_id = hospital_response.json()["id"]

    doctor_response = client.post(
        "/api/v1/admin/doctors",
        json={
            "full_name": "Dr. Example Person",
            "specialty": "General Medicine",
            "is_demo": True,
            "source_name": "Fictional test data",
        },
    )
    assert doctor_response.status_code == 201
    doctor = doctor_response.json()
    doctor_id = doctor["id"]
    assert doctor["profile_status"] == "draft"
    assert doctor["is_demo"] is True

    affiliation_response = client.post(
        f"/api/v1/admin/doctors/{doctor_id}/affiliations",
        json={
            "hospital_id": hospital_id,
            "role_title": "Demo Consultant",
            "status": "current",
            "is_demo": True,
            "source_name": "Fictional test data",
        },
    )
    assert affiliation_response.status_code == 201
    assert len(affiliation_response.json()["affiliations"]) == 1
    assert affiliation_response.json()["affiliations"][0]["hospital"]["name"] == "Demo Hospital"


def test_admin_routes_reject_patient(client):
    patient = _user("patient")
    app.dependency_overrides[get_current_user] = lambda: patient

    response = client.get("/api/v1/admin/doctors")
    assert response.status_code == 403


def test_admin_routes_reject_anonymous_user(client):
    response = client.get("/api/v1/admin/doctors")
    assert response.status_code == 401


def test_hospital_coordinates_must_be_a_pair(client):
    admin = _user("admin")
    app.dependency_overrides[get_current_user] = lambda: admin
    response = client.post(
        "/api/v1/admin/hospitals",
        json={
            "name": "Demo Hospital",
            "address": "1 Example Street",
            "city": "Demo City",
            "latitude": 22.5,
        },
    )
    assert response.status_code == 422
