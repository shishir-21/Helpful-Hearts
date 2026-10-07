from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.integrations.ai.openai_provider import OpenAIProvider
from app.integrations.ai.provider import ProviderError


def _register(client: TestClient, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": "Test Patient", "password": "strong-pass-123"},
    )
    assert response.status_code == 201
    return response.json()


def test_patient_can_create_and_read_assistant_conversation(client):
    auth = _register(client, "assistant@example.com")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}

    created = client.post("/api/v1/assistant/conversations", json={"title": "Health questions"}, headers=headers)
    assert created.status_code == 201
    conversation = created.json()
    assert conversation["title"] == "Health questions"

    listed = client.get("/api/v1/assistant/conversations", headers=headers)
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == conversation["id"]


def test_assistant_conversation_is_private(client):
    first = _register(client, "first@example.com")
    second = _register(client, "second@example.com")
    first_headers = {"Authorization": f"Bearer {first['access_token']}"}
    second_headers = {"Authorization": f"Bearer {second['access_token']}"}

    created = client.post("/api/v1/assistant/conversations", headers=first_headers, json={})
    conversation_id = created.json()["id"]

    response = client.get(
        f"/api/v1/assistant/conversations/{conversation_id}/messages",
        headers=second_headers,
    )
    assert response.status_code == 404


def test_assistant_message_is_generated_and_persisted(client, monkeypatch: pytest.MonkeyPatch):
    auth = _register(client, "message@example.com")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    conversation = client.post("/api/v1/assistant/conversations", headers=headers, json={}).json()

    monkeypatch.setattr(OpenAIProvider, "generate", lambda self, messages: "General health information.")
    response = client.post(
        f"/api/v1/assistant/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"content": "What is a fever?"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "assistant"

    messages = client.get(
        f"/api/v1/assistant/conversations/{conversation['id']}/messages",
        headers=headers,
    )
    assert [item["role"] for item in messages.json()] == ["user", "assistant"]


def test_provider_failure_returns_service_unavailable(client, monkeypatch: pytest.MonkeyPatch):
    auth = _register(client, "failure@example.com")
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    conversation = client.post("/api/v1/assistant/conversations", headers=headers, json={}).json()

    def fail(self, messages):
        raise ProviderError("AI provider is not configured")

    monkeypatch.setattr(OpenAIProvider, "generate", fail)
    response = client.post(
        f"/api/v1/assistant/conversations/{conversation['id']}/messages",
        headers=headers,
        json={"content": "Hello"},
    )
    assert response.status_code == 503
