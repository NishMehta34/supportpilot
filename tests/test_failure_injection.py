"""Failure injection: break things on purpose and prove the app stays safe."""

import json

import pytest

from app.agent_loop import run_agent
from app.agent_tools import AGENT_TOOL_FUNCTIONS
from app.classifier import ClassificationError, classify_message
from app.model_adapter import FakeAdapter


def tool_call(name, **arguments):
    return {"role": "assistant", "content": "",
            "tool_calls": [{"function": {"name": name, "arguments": arguments}}]}


def test_a_tool_that_crashes_is_contained():
    def explode(**kwargs):
        raise RuntimeError("boom")

    AGENT_TOOL_FUNCTIONS["explode"] = explode
    try:
        fake = FakeAdapter([tool_call("explode"), "Sorry, that failed."])
        result = run_agent("break it", chat_fn=fake.tool_chat_fn())
    finally:
        del AGENT_TOOL_FUNCTIONS["explode"]  # always clean up the booby trap
    assert result["stop_reason"] == "final_answer"
    assert "boom" in result["trace"][0]["result"]["error"]


def test_an_unknown_tool_is_refused_not_run():
    fake = FakeAdapter([tool_call("delete_all_data"), "I can't do that."])
    result = run_agent("be evil", chat_fn=fake.tool_chat_fn())
    assert "Unknown tool" in result["trace"][0]["result"]["error"]
    assert result["stop_reason"] == "final_answer"


def test_malformed_model_output_never_reaches_business_logic():
    fake = FakeAdapter(["not json at all"], repeat_last=True)
    with pytest.raises(ClassificationError):
        classify_message("help", chat_fn=fake.json_chat_fn(), max_attempts=2)
    assert len(fake.calls) == 2  # it tried twice, then gave up


def test_an_endless_agent_is_stopped_at_the_step_limit():
    fake = FakeAdapter([tool_call("get_order", order_id=f"ORD-{n}") for n in range(20)])
    result = run_agent("never ends", chat_fn=fake.tool_chat_fn(), max_steps=6)
    assert result["stop_reason"] == "max_steps_reached"
    assert result["steps_used"] == 6
    assert len(fake.calls) == 6


def test_an_agent_repeating_itself_is_cut_off_early():
    fake = FakeAdapter([tool_call("get_order", order_id="ORD-1001")], repeat_last=True)
    result = run_agent("loop", chat_fn=fake.tool_chat_fn())
    assert result["stop_reason"] == "stuck_in_loop"
    assert result["steps_used"] < 6


def test_arguments_sent_as_broken_text_do_not_crash_the_agent():
    broken = {"role": "assistant", "content": "",
              "tool_calls": [{"function": {"name": "get_order", "arguments": "{not valid json"}}]}
    result = run_agent("x", chat_fn=FakeAdapter([broken, "Which order?"]).tool_chat_fn())
    assert "error" in result["trace"][0]["result"]
    assert result["stop_reason"] == "final_answer"


def test_an_empty_model_reply_ends_the_agent_cleanly():
    result = run_agent("x", chat_fn=FakeAdapter([{"role": "assistant", "content": ""}]).tool_chat_fn())
    assert result["stop_reason"] == "final_answer"
    assert result["final_answer"] == ""
