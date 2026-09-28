"""Tests for the model adapters. No real model is needed."""

import json
import urllib.error

import pytest

from app.classifier import classify_message
from app.model_adapter import FakeAdapter, OllamaAdapter
from app.tool_loop import answer_with_tools

GOOD_JSON = json.dumps(
    {"category": "billing", "priority": "high", "summary": "Charged twice.", "confidence": 0.9}
)


def test_fake_adapter_returns_scripted_replies_in_order():
    fake = FakeAdapter([{"role": "assistant", "content": "one"}, "two"])
    assert fake.chat([])["content"] == "one"
    assert fake.chat([])["content"] == "two"


def test_fake_adapter_turns_plain_text_into_a_message():
    assert FakeAdapter(["hello"]).chat([]) == {"role": "assistant", "content": "hello"}


def test_fake_adapter_records_every_call():
    fake = FakeAdapter(["a"])
    fake.chat([{"role": "user", "content": "hi"}], tools=["T"], schema={"x": 1})
    call = fake.calls[0]
    assert call["messages"][0]["content"] == "hi"
    assert call["tools"] == ["T"]
    assert call["schema"] == {"x": 1}


def test_fake_adapter_fails_loudly_when_the_script_runs_out():
    fake = FakeAdapter(["only one"])
    fake.chat([])
    with pytest.raises(RuntimeError, match="ran out"):
        fake.chat([])


def test_fake_adapter_can_repeat_its_last_reply():
    fake = FakeAdapter(["again"], repeat_last=True)
    assert [fake.chat([])["content"] for _ in range(3)] == ["again"] * 3


def test_ollama_adapter_builds_a_plain_request():
    posted = {}

    def fake_post(url, body):
        posted.update(url=url, body=body)
        return {"message": {"role": "assistant", "content": "hi"}}

    reply = OllamaAdapter(model="test-model", http_post=fake_post).chat(
        [{"role": "user", "content": "yo"}]
    )
    assert reply["content"] == "hi"
    assert posted["body"]["model"] == "test-model"
    assert posted["body"]["stream"] is False
    assert "tools" not in posted["body"] and "format" not in posted["body"]


def test_ollama_adapter_sends_tools_and_schema_only_when_given():
    posted = {}

    def fake_post(url, body):
        posted["body"] = body
        return {"message": {"role": "assistant", "content": ""}}

    adapter = OllamaAdapter(http_post=fake_post)
    adapter.chat([], tools=[{"type": "function"}], schema={"type": "object"})
    assert posted["body"]["tools"] == [{"type": "function"}]
    assert posted["body"]["format"] == {"type": "object"}


def test_ollama_adapter_lets_connection_errors_through():
    def broken_post(url, body):
        raise urllib.error.URLError("connection refused")

    with pytest.raises(urllib.error.URLError):
        OllamaAdapter(http_post=broken_post).chat([])


def test_fake_adapter_plugs_into_the_tool_loop():
    fake = FakeAdapter([
        {"role": "assistant", "content": "",
         "tool_calls": [{"function": {"name": "get_order", "arguments": {"order_id": "ORD-1001"}}}]},
        "Your order has shipped.",
    ])
    run = answer_with_tools("Where is ORD-1001?", chat_fn=fake.tool_chat_fn())
    assert run["final_answer"] == "Your order has shipped."
    assert len(fake.calls) == 2


def test_fake_adapter_plugs_into_the_classifier():
    fake = FakeAdapter([GOOD_JSON])
    assert classify_message("help", chat_fn=fake.json_chat_fn()).category == "billing"
