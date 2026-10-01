"""A bounded agent: think -> act -> observe, with hard stop conditions."""

import json
import time
from pathlib import Path

from app.agent_tools import AGENT_TOOL_SCHEMAS, execute_agent_tool
from app.tool_calls import parse_tool_call
from app.tool_loop import ollama_chat

MAX_STEPS = 6          # hard limit on model calls per task
MAX_DUPLICATES = 2     # stop if the agent keeps repeating the same call

SYSTEM_PROMPT = (
    "You are a customer support agent. Solve the task step by step using the tools. "
    "Look things up with tools instead of guessing, and use the calculator for any maths. "
    "You may call several tools over several steps. When you have everything you need, "
    "reply with a short final answer and no tool call. Never invent data."
)


def run_agent(task, chat_fn=ollama_chat, max_steps=MAX_STEPS,
              tool_schemas=AGENT_TOOL_SCHEMAS, execute_tool=execute_agent_tool):
    """The loop itself doesn't care WHICH tools it's given (SupportPilot's order
    tools, Alfred's party-planning tools, anything). That's what makes it a
    reusable primitive rather than a one-off script. Day 11 proves this by
    reusing the exact same loop with a completely different toolbox.

    Always returns a result with a stop_reason and a full trace."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]
    trace = []
    seen_calls = set()
    duplicates = 0
    started = time.perf_counter()

    def finish(stop_reason, final_answer=None):
        return {
            "task": task,
            "stop_reason": stop_reason,       # final_answer | max_steps_reached | stuck_in_loop
            "final_answer": final_answer,
            "steps_used": step,
            "max_steps": max_steps,
            "total_ms": round((time.perf_counter() - started) * 1000),
            "trace": trace,
        }

    step = 0
    for step in range(1, max_steps + 1):
        # THINK: the model decides what to do next.
        reply = chat_fn(messages, tool_schemas)
        messages.append(reply)
        calls = reply.get("tool_calls") or []

        # STOP CONDITION 1: no tool requested -> the model gave its final answer.
        if not calls:
            trace.append({"step": step, "type": "final_answer", "content": reply.get("content", "")})
            return finish("final_answer", reply.get("content", ""))

        # ACT + OBSERVE: run each requested tool and hand the result back.
        for call in calls:
            name, arguments = parse_tool_call(call)  # safe even if the call is malformed

            signature = (name, json.dumps(arguments, sort_keys=True))
            began = time.perf_counter()
            if signature in seen_calls:
                duplicates += 1
                result = {"error": "You already made this exact call. Use the earlier result."}
            else:
                seen_calls.add(signature)
                result = execute_tool(name, arguments)

            trace.append({
                "step": step, "type": "tool_call", "tool": name, "arguments": arguments,
                "result": result, "elapsed_ms": round((time.perf_counter() - began) * 1000, 2),
            })
            messages.append({"role": "tool", "tool_name": name, "content": json.dumps(result)})

        # STOP CONDITION 2: the agent is going in circles.
        if duplicates >= MAX_DUPLICATES:
            return finish("stuck_in_loop")

    # STOP CONDITION 3: step budget used up.
    return finish("max_steps_reached")


def save_trace(result, path):
    """Write a run's full trace to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2))
    return path
