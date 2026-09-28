"""A bounded agent: Think -> Act -> Observe, repeated, with hard stop conditions."""

import json
import time
from pathlib import Path

from app.agent_tools import AGENT_SCHEMAS, execute_agent_tool
from app.tool_loop import MODEL, ollama_chat

MAX_STEPS = 6          # the model may be called at most this many times
MAX_DUPLICATES = 2     # stop if the model keeps repeating identical tool calls

SYSTEM_PROMPT = (
    "You are a customer support agent. Solve the task step by step using the "
    "tools. Use the calculator for ANY arithmetic. Look things up instead of "
    "guessing. Do not repeat a tool call you already made. When you have "
    "everything you need, give a short final answer."
)

FALLBACK_ANSWER = "I could not finish this task within the allowed number of steps."


def run_agent(task, chat_fn=ollama_chat, max_steps=MAX_STEPS):
    """Run the agent on a task. ALWAYS returns, in at most max_steps model calls.

    Stop conditions: final_answer, max_steps_reached, repeated_call.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]
    steps = []
    seen_calls = set()
    duplicates = 0
    stop_reason = "max_steps_reached"
    final_answer = None
    started = time.perf_counter()

    for step_number in range(1, max_steps + 1):
        reply = chat_fn(messages, AGENT_SCHEMAS)          # THINK
        messages.append(reply)
        calls = reply.get("tool_calls") or []
        step = {"step": step_number, "model_content": reply.get("content", ""), "tool_calls": []}
        steps.append(step)

        if not calls:                                      # STOP: model is done
            final_answer = reply.get("content", "")
            stop_reason = "final_answer"
            break

        for call in calls:                                 # ACT
            name = call["function"]["name"]
            arguments = call["function"]["arguments"]
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    arguments = {}

            key = (name, json.dumps(arguments, sort_keys=True))
            began = time.perf_counter()
            if key in seen_calls:
                duplicates += 1
                result = {"error": "Duplicate call skipped. Use the earlier result."}
            else:
                seen_calls.add(key)
                result = execute_agent_tool(name, arguments)
            step["tool_calls"].append({
                "name": name,
                "arguments": arguments,
                "result": result,
                "duration_ms": round((time.perf_counter() - began) * 1000, 2),
            })
            # OBSERVE: hand the result back to the model
            messages.append({"role": "tool", "tool_name": name, "content": json.dumps(result)})

        if duplicates >= MAX_DUPLICATES:                   # STOP: model is looping
            stop_reason = "repeated_call"
            break

    if final_answer is None:
        final_answer = FALLBACK_ANSWER

    return {
        "task": task,
        "model": MODEL,
        "max_steps": max_steps,
        "steps_used": len(steps),
        "stop_reason": stop_reason,
        "final_answer": final_answer,
        "total_ms": round((time.perf_counter() - started) * 1000, 2),
        "steps": steps,
    }


def save_trace(run, path):
    """Write the step-by-step trace of one run to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(run, indent=2))
    return path
