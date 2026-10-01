"""Tests for the FastAPI /ask endpoint itself, using FastAPI's TestClient.

The real database and model are replaced with fakes via dependency overrides,
so this test file needs `fastapi` installed but never needs Ollama or Postgres
running.
"""

import pytest

fastapi_testclient = pytest.importorskip("fastapi.testclient")

from fastapi.testclient import TestClient

from app import main
from app.rag import NOT_FOUND_MESSAGE


@pytest.fixture
def client(monkeypatch):
    def fake_retrieve(question, tenant_id, k):
        if "weather" in question.lower():
            return []
        return [{
            "doc_id": "KB-RETURNS", "section": "Return window",
            "content": "Standard members have 30 days to return an item.", "score": 0.9,
        }]

    def fake_chat_fn(messages):
        user_message = messages[-1]["content"]
        if "weather" in user_message.lower():
            return NOT_FOUND_MESSAGE
        return "You have 30 days to return an item [S1]."

    monkeypatch.setattr(main, "_retrieve", fake_retrieve)
    monkeypatch.setattr(main, "_chat_fn", fake_chat_fn)
    return TestClient(main.app)


def test_health_endpoint():
    client = TestClient(main.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ask_returns_a_cited_answer(client):
    response = client.post("/ask", json={"question": "How long can I return an item?", "tenant_id": "nimbus"})
    assert response.status_code == 200
    body = response.json()
    assert body["not_found"] is False
    assert len(body["sources"]) == 1
    assert body["sources"][0]["doc_id"] == "KB-RETURNS"
    assert "[S1]" in body["answer"]


def test_ask_returns_not_found_for_out_of_scope_question(client):
    response = client.post("/ask", json={"question": "What's the weather today?", "tenant_id": "nimbus"})
    assert response.status_code == 200
    body = response.json()
    assert body["not_found"] is True
    assert body["sources"] == []


def test_ask_rejects_an_empty_question():
    client = TestClient(main.app)
    response = client.post("/ask", json={"question": "", "tenant_id": "nimbus"})
    assert response.status_code == 422  # FastAPI's validation error


def test_ask_rejects_a_missing_tenant_id():
    client = TestClient(main.app)
    response = client.post("/ask", json={"question": "hello"})
    assert response.status_code == 422
