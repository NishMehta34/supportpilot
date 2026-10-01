"""Tests for MiniAgent (Day 12, version 3). No real model needed."""

from app.mini_agent import MiniAgent


def tool_call(name, **args):
    return {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": name, "arguments": args}}]}


def scripted(*replies):
    remaining = list(replies)
    return lambda messages, tools: remaining.pop(0)


def fake_execute(name, arguments):
    return {"ok": True, "name": name, "arguments": arguments}


def test_run_returns_the_final_answer_as_a_plain_string():
    chat = scripted({"role": "assistant", "content": "Done."})
    agent = MiniAgent(chat_fn=chat, tools=[], execute_tool=fake_execute)
    assert agent.run("task") == "Done."


def test_run_can_use_a_tool_first():
    chat = scripted(tool_call("get_order", order_id="ORD-1001"), {"role": "assistant", "content": "Shipped."})
    agent = MiniAgent(chat_fn=chat, tools=[], execute_tool=fake_execute)
    assert agent.run("task") == "Shipped."


def test_explain_last_run_before_any_run():
    agent = MiniAgent(chat_fn=lambda m, t: {"content": "x"}, tools=[], execute_tool=fake_execute)
    assert agent.explain_last_run() == "No run yet."


def test_explain_last_run_summarizes_the_trace():
    chat = scripted(tool_call("get_order", order_id="ORD-1001"), {"role": "assistant", "content": "Shipped."})
    agent = MiniAgent(chat_fn=chat, tools=[], execute_tool=fake_execute)
    agent.run("task")
    summary = agent.explain_last_run()
    assert "final_answer" in summary
    assert "get_order" in summary


def test_respects_a_custom_max_steps():
    chat = lambda messages, tools: tool_call("get_order", order_id="ORD-1001")
    agent = MiniAgent(chat_fn=chat, tools=[], execute_tool=fake_execute, max_steps=3)
    agent.run("loops forever")
    assert agent.last_result["steps_used"] <= 3
