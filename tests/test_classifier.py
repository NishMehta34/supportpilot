"""Tests use a FAKE model, so no Ollama is needed."""

import json

import pytest

from app.classifier import ClassificationError, classify_message

GOOD = json.dumps(
    {"category": "billing", "priority": "high", "summary": "Charged twice.", "confidence": 0.9}
)


def fake_model(*replies):
    """Build a fake chat function that returns the given replies in order."""
    calls = {"count": 0}
    remaining = list(replies)

    def chat(messages, schema):
        calls["count"] += 1
        return remaining.pop(0) if len(remaining) > 1 else remaining[0]

    chat.calls = calls
    return chat


def test_valid_output_is_accepted():
    result = classify_message("help", chat_fn=fake_model(GOOD))
    assert result.category == "billing"
    assert result.confidence == 0.9


def test_malformed_json_is_rejected_after_retries():
    chat = fake_model("this is not json")
    with pytest.raises(ClassificationError):
        classify_message("help", chat_fn=chat, max_attempts=3)
    assert chat.calls["count"] == 3


def test_unknown_category_is_rejected():
    bad = json.dumps({"category": "pizza", "priority": "low", "summary": "x", "confidence": 0.5})
    with pytest.raises(ClassificationError):
        classify_message("help", chat_fn=fake_model(bad))


def test_confidence_out_of_range_is_rejected():
    bad = json.dumps({"category": "billing", "priority": "low", "summary": "x", "confidence": 7})
    with pytest.raises(ClassificationError):
        classify_message("help", chat_fn=fake_model(bad))


def test_missing_field_is_rejected():
    bad = json.dumps({"category": "billing", "priority": "low"})
    with pytest.raises(ClassificationError):
        classify_message("help", chat_fn=fake_model(bad))


def test_retry_recovers_after_one_bad_answer():
    chat = fake_model("garbage", GOOD)
    result = classify_message("help", chat_fn=chat)
    assert result.category == "billing"
    assert chat.calls["count"] == 2
