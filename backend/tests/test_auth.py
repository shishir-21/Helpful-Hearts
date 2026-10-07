from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user, get_db, require_roles
from app.core.config import settings
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
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
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


def test_register_and_current_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "Patient@example.com", "full_name": "Test Patient", "password": "strong-pass-123"},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["user"]["email"] == "patient@example.com"
    assert payload["user"]["role"] == "patient"
    assert "password" not in payload["user"]
    assert payload["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {payload['access_token']}"})
    assert me.status_code == 200
    assert me.json()["id"] == payload["user"]["id"]


def test_duplicate_email_is_rejected(client):
    data = {"email": "same@example.com", "full_name": "Test Patient", "password": "strong-pass-123"}
    assert client.post("/api/v1/auth/register", json=data).status_code == 201
    duplicate = {**data, "email": "SAME@example.com"}
    assert client.post("/api/v1/auth/register", json=duplicate).status_code == 409


def test_invalid_credentials_are_rejected(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "patient@example.com", "full_name": "Test Patient", "password": "strong-pass-123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "patient@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_protected_route_rejects_missing_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_expired_token_is_rejected(client):
    expired = jwt.encode(
        {"sub": str(uuid4()), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        settings.secret_key,
        algorithm="HS256",
    )
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_role_dependency_rejects_patient():
    test_app = FastAPI()
    patient = User(
        id=uuid4(),
        email="patient@example.com",
        full_name="Test Patient",
        password_hash="not-used",
        role="patient",
        is_active=True,
    )

    @test_app.get("/admin")
    def admin_only(_user: User = Depends(require_roles("admin"))):
        return {"ok": True}

    test_app.dependency_overrides[get_current_user] = lambda: patient
    response = TestClient(test_app).get("/admin")
    assert response.status_code == 403


def test_login_succeeds_after_registration(client):
    password = "strong-pass-123"
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": "Patient@example.com", "full_name": "Test Patient", "password": password},
    )
    assert registered.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "  PATIENT@example.com  ", "password": password},
    )
    assert login.status_code == 200
    payload = login.json()
    assert payload["user"]["email"] == "patient@example.com"
    assert payload["user"]["id"] == registered.json()["user"]["id"]
    assert payload["access_token"]
