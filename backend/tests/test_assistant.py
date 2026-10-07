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
from app.services import assistant as assistant_service


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
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


def patient() -> User:
    return User(id=uuid4(), email=f"{uuid4()}@example.com", full_name="Test Patient", password_hash="unused", role="patient")


def test_assistant_requires_authentication(client):
    assert client.get("/api/v1/assistant/conversations").status_code == 401


def test_patient_can_create_list_and_read_conversation_messages(client, monkeypatch):
    current = patient()
    app.dependency_overrides[get_current_user] = lambda: current

    created = client.post("/api/v1/assistant/conversations", json={"title": "My health questions"})
    assert created.status_code == 201
    conversation_id = created.json()["id"]

    class FakeProvider:
        async def generate(self, messages):
            assert messages[-1] == {"role": "user", "content": "What can cause a mild headache?"}
            return "A mild headache can have many causes. If it is severe, sudden, persistent, or accompanied by concerning symptoms, seek medical care."

    monkeypatch.setattr(assistant_service, "get_assistant_provider", lambda: FakeProvider())
    sent = client.post(
        f"/api/v1/assistant/conversations/{conversation_id}/messages",
        json={"content": "What can cause a mild headache?"},
    )
    assert sent.status_code == 201
    assert sent.json()["role"] == "assistant"

    listed = client.get("/api/v1/assistant/conversations")
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == conversation_id

    messages = client.get(f"/api/v1/assistant/conversations/{conversation_id}/messages")
    assert messages.status_code == 200
    assert [item["role"] for item in messages.json()] == ["user", "assistant"]


def test_patient_cannot_access_another_patients_conversation(client):
    owner = patient()
    other = patient()
    app.dependency_overrides[get_current_user] = lambda: owner
    created = client.post("/api/v1/assistant/conversations", json={})
    conversation_id = created.json()["id"]

    app.dependency_overrides[get_current_user] = lambda: other
    assert client.get(f"/api/v1/assistant/conversations/{conversation_id}/messages").status_code == 404
    assert client.post(
        f"/api/v1/assistant/conversations/{conversation_id}/messages",
        json={"content": "Hello"},
    ).status_code == 404


def test_assistant_provider_failure_does_not_persist_user_message(client, monkeypatch):
    current = patient()
    app.dependency_overrides[get_current_user] = lambda: current
    created = client.post("/api/v1/assistant/conversations", json={})
    conversation_id = created.json()["id"]

    async def fail(_messages):
        raise assistant_service.AssistantProviderError("AI provider is not configured")

    class FailingProvider:
        generate = fail

    monkeypatch.setattr(assistant_service, "get_assistant_provider", lambda: FailingProvider())
    response = client.post(
        f"/api/v1/assistant/conversations/{conversation_id}/messages",
        json={"content": "Hello"},
    )
    assert response.status_code == 503
    messages = client.get(f"/api/v1/assistant/conversations/{conversation_id}/messages")
    assert messages.json() == []


def test_assistant_rejects_empty_or_oversized_messages(client):
    current = patient()
    app.dependency_overrides[get_current_user] = lambda: current
    created = client.post("/api/v1/assistant/conversations", json={})
    conversation_id = created.json()["id"]

    assert client.post(
        f"/api/v1/assistant/conversations/{conversation_id}/messages", json={"content": ""}
    ).status_code == 422
    assert client.post(
        f"/api/v1/assistant/conversations/{conversation_id}/messages", json={"content": "x" * 4001}
    ).status_code == 422


def test_only_patients_can_use_assistant(client):
    doctor = User(id=uuid4(), email=f"{uuid4()}@example.com", full_name="Test Doctor", password_hash="unused", role="doctor")
    app.dependency_overrides[get_current_user] = lambda: doctor
    assert client.get("/api/v1/assistant/conversations").status_code == 403
    assert client.post("/api/v1/assistant/conversations", json={}).status_code == 403
