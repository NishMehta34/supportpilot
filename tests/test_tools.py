"""Tests for the toolbox and the tool loop. A FAKE model is used: no Ollama needed."""

from app.tool_loop import answer_with_tools
from app.tools import execute_tool


def test_get_order_returns_data():
    assert execute_tool("get_order", {"order_id": "ORD-1001"})["status"] == "shipped"


def test_missing_record_returns_error_not_crash():
    assert "error" in execute_tool("get_order", {"order_id": "ORD-9999"})


def test_unknown_tool_returns_error():
    assert "Unknown tool" in execute_tool("delete_everything", {})["error"]


def test_wrong_arguments_return_error():
    assert "error" in execute_tool("get_order", {"wrong_name": "x"})


def fake_model(*replies):
    """A fake model that returns the given reply messages in order."""
    remaining = list(replies)
    return lambda messages, tools: remaining.pop(0)


def test_loop_selects_executes_and_answers():
    tool_call = {"role": "assistant", "content": "",
                 "tool_calls": [{"function": {"name": "get_order", "arguments": {"order_id": "ORD-1001"}}}]}
    final = {"role": "assistant", "content": "Your order has shipped."}
    run = answer_with_tools("Where is ORD-1001?", chat_fn=fake_model(tool_call, final))

    assert run["tools_called"][0]["name"] == "get_order"
    assert run["tools_called"][0]["result"]["status"] == "shipped"
    assert run["final_answer"] == "Your order has shipped."
    assert any(m["role"] == "tool" for m in run["messages"])  # result was passed back


def test_loop_without_tool_call_returns_direct_answer():
    direct = {"role": "assistant", "content": "Please tell me your order ID."}
    run = answer_with_tools("Where is my order?", chat_fn=fake_model(direct))
    assert run["tools_called"] == []
    assert run["final_answer"] == "Please tell me your order ID."


def test_loop_survives_unknown_tool_from_model():
    bad_call = {"role": "assistant", "content": "",
                "tool_calls": [{"function": {"name": "hack_system", "arguments": {}}}]}
    final = {"role": "assistant", "content": "Sorry, I can't do that."}
    run = answer_with_tools("do bad things", chat_fn=fake_model(bad_call, final))
    assert "error" in run["tools_called"][0]["result"]
    assert run["final_answer"] == "Sorry, I can't do that."
