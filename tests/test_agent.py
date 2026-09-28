"""Tests for the calculator, order search and bounded agent loop. FAKE model: no Ollama needed."""

import json
import tempfile
from pathlib import Path

from app.agent_loop import run_agent, save_trace
from app.agent_tools import calculator, execute_agent_tool, search_orders


def call(name, **arguments):
    return {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": name, "arguments": arguments}}]}


def answer(text):
    return {"role": "assistant", "content": text}


def scripted(*replies):
    """Fake model returning the given replies in order."""
    remaining = list(replies)
    return lambda messages, tools: remaining.pop(0)


def test_calculator_basic():
    assert calculator("24.99 * 3")["result"] == 74.97


def test_calculator_rejects_code():
    assert "error" in calculator("__import__('os').system('ls')")


def test_calculator_division_by_zero():
    assert calculator("1 / 0")["error"] == "Division by zero"


def test_search_orders_by_customer():
    assert search_orders(customer_id="CUS-001")["count"] == 2


def test_search_orders_by_status():
    result = search_orders(status="processing")
    assert result["count"] == 1 and result["orders"][0]["order_id"] == "ORD-1002"


def test_multi_step_run_finishes_with_answer():
    model = scripted(call("get_order", order_id="ORD-1001"),
                     call("get_product", product_id="PRD-001"),
                     answer("The mouse costs 24.99."))
    run = run_agent("price?", chat_fn=model)
    assert run["stop_reason"] == "final_answer"
    assert run["steps_used"] == 3
    assert run["final_answer"] == "The mouse costs 24.99."


def test_max_steps_limit_is_enforced():
    counter = {"n": 0}

    def endless(messages, tools):  # a different call every time, never finishes
        counter["n"] += 1
        return call("get_order", order_id=f"ORD-{counter['n']}")

    run = run_agent("loop forever", chat_fn=endless, max_steps=6)
    assert run["stop_reason"] == "max_steps_reached"
    assert run["steps_used"] == 6
    assert counter["n"] == 6


def test_repeated_call_stops_the_agent():
    def stuck(messages, tools):
        return call("get_order", order_id="ORD-1001")

    run = run_agent("stuck", chat_fn=stuck, max_steps=6)
    assert run["stop_reason"] == "stuck_in_loop"
    assert run["steps_used"] < 6


def test_unknown_tool_does_not_crash_the_loop():
    model = scripted(call("hack_system"), answer("Sorry, I cannot do that."))
    run = run_agent("bad", chat_fn=model)
    assert "error" in run["trace"][0]["result"]
    assert run["stop_reason"] == "final_answer"


def test_trace_is_saved_as_json():
    run = run_agent("hi", chat_fn=scripted(answer("hello")))
    with tempfile.TemporaryDirectory() as folder:
        path = save_trace(run, Path(folder) / "trace.json")
        saved = json.loads(path.read_text())
    assert saved["task"] == "hi" and saved["steps_used"] == 1
