"""Regression tests: each one pins down a real bug so it can never come back.

Bug 1 - valid answers rejected because the model wrapped them in extra text.
Bug 2 - a malformed tool call from the model crashed the loops.
Bug 3 - IDs like 'ord-1001' or status 'Shipped' were "not found".
"""

import json

import pytest

from app.agent_loop import run_agent
from app.agent_tools import search_orders
from app.classifier import ClassificationError, classify_message
from app.model_adapter import FakeAdapter
from app.tool_loop import answer_with_tools
from app.tools import get_customer, get_order, get_product

GOOD = json.dumps(
    {"category": "billing", "priority": "high", "summary": "Charged twice.", "confidence": 0.9}
)


def classify(reply, **kwargs):
    fake = FakeAdapter([reply], repeat_last=True)
    return classify_message("help", chat_fn=fake.json_chat_fn(), **kwargs)


# ---------- Bug 1: answer wrapped in extra text ----------
def test_bug1_json_inside_a_code_fence_is_accepted():
    assert classify("```json\n" + GOOD + "\n```").category == "billing"


def test_bug1_json_after_a_think_block_is_accepted():
    assert classify("<think>Let me consider this...</think>\n" + GOOD).category == "billing"


def test_bug1_json_with_a_chatty_intro_is_accepted():
    assert classify("Sure! Here is the JSON: " + GOOD + " Hope that helps!").category == "billing"


def test_bug1_guard_plain_text_is_still_rejected():
    with pytest.raises(ClassificationError):
        classify("I am unable to classify this.", max_attempts=2)


def test_bug1_guard_invalid_values_inside_a_fence_are_still_rejected():
    bad = json.dumps({"category": "pizza", "priority": "low", "summary": "x", "confidence": 0.5})
    with pytest.raises(ClassificationError):
        classify("```json\n" + bad + "\n```", max_attempts=2)


# ---------- Bug 2: malformed tool calls ----------
def test_bug2_tool_loop_survives_a_call_without_arguments():
    call = {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "get_order"}}]}
    run = answer_with_tools("where is it?", chat_fn=FakeAdapter([call, "Which order?"]).tool_chat_fn())
    assert "error" in run["tools_called"][0]["result"]
    assert run["final_answer"] == "Which order?"


def test_bug2_agent_survives_a_call_without_arguments():
    call = {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "get_order"}}]}
    result = run_agent("where is it?", chat_fn=FakeAdapter([call, "Which order?"]).tool_chat_fn())
    assert result["stop_reason"] == "final_answer"


def test_bug2_agent_survives_a_call_without_a_name():
    call = {"role": "assistant", "content": "", "tool_calls": [{"function": {"arguments": {}}}]}
    result = run_agent("odd", chat_fn=FakeAdapter([call, "Sorry."]).tool_chat_fn())
    assert result["stop_reason"] == "final_answer"


def test_bug2_agent_survives_a_call_without_a_function():
    call = {"role": "assistant", "content": "", "tool_calls": [{}]}
    result = run_agent("odd", chat_fn=FakeAdapter([call, "Sorry."]).tool_chat_fn())
    assert result["stop_reason"] == "final_answer"


# ---------- Bug 3: capitalisation and stray spaces ----------
def test_bug3_order_lookup_ignores_case_and_spaces():
    assert get_order("  ord-1001 ")["status"] == "shipped"


def test_bug3_customer_and_product_lookup_ignore_case():
    assert get_customer("cus-001")["name"] == "Asha Patel"
    assert get_product("prd-002")["name"] == "Mechanical Keyboard"


def test_bug3_order_search_ignores_case():
    assert search_orders(status="Processing")["count"] == 1
    assert search_orders(customer_id="cus-001")["count"] == 2


def test_bug3_guard_unknown_ids_are_still_not_found():
    assert "error" in get_order("nope")
    assert "error" in get_customer("CUS-999")
