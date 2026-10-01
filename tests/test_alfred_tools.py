"""Tests for the Alfred tools, and proof that Day 4's agent loop genuinely
works with a completely different toolbox (not just SupportPilot's)."""

from app.agent_loop import run_agent
from app.alfred_tools import ALFRED_TOOL_SCHEMAS, check_guest, check_weather, execute_alfred_tool


def test_check_weather_returns_data():
    assert check_weather("Gotham")["condition"] == "light rain"


def test_check_guest_is_case_insensitive():
    assert check_guest("SELINA KYLE")["relation"] == "guest of honour"


def test_unknown_guest_returns_an_error_not_a_crash():
    assert "error" in check_guest("The Joker")


def test_unknown_tool_name_returns_an_error():
    assert "Unknown tool" in execute_alfred_tool("steal_the_batmobile", {})["error"]


def tool_call(name, **arguments):
    return {"role": "assistant", "content": "",
            "tool_calls": [{"function": {"name": name, "arguments": arguments}}]}


def scripted(*replies):
    remaining = list(replies)
    return lambda messages, tools: remaining.pop(0)


def test_the_same_run_agent_works_with_alfreds_tools_not_just_supportpilots():
    """The real point of Day 11: run_agent has no idea it's planning a party
    instead of looking up an order. The loop is a reusable primitive."""
    chat = scripted(
        tool_call("check_weather", city="Gotham"),
        tool_call("suggest_playlist", mood="elegant"),
        {"role": "assistant", "content": "It's rainy, so an elegant indoor playlist suits the mood."},
    )
    result = run_agent(
        "Plan the party vibe", chat_fn=chat,
        tool_schemas=ALFRED_TOOL_SCHEMAS, execute_tool=execute_alfred_tool,
    )
    tools_used = [step["tool"] for step in result["trace"] if step["type"] == "tool_call"]
    assert tools_used == ["check_weather", "suggest_playlist"]
    assert result["stop_reason"] == "final_answer"


def test_alfred_agent_still_respects_the_step_limit():
    """Same safety guarantee as Day 4, now proven on a different toolbox too."""
    chat = lambda messages, tools: tool_call("check_weather", city="Gotham")
    result = run_agent(
        "loop forever", chat_fn=chat, max_steps=6,
        tool_schemas=ALFRED_TOOL_SCHEMAS, execute_tool=execute_alfred_tool,
    )
    assert result["stop_reason"] == "stuck_in_loop"
    assert result["steps_used"] < 6
