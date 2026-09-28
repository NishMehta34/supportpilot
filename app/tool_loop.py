"""Let the model pick a tool, run it, and turn the result into a final answer."""

import json
import urllib.request

from app.tool_calls import parse_tool_call
from app.tools import TOOL_SCHEMAS, execute_tool

MODEL = "qwen3"
URL = "http://localhost:11434/api/chat"

SYSTEM_PROMPT = (
    "You are a customer support assistant. Use the tools to look up orders, "
    "customers and products. If the user has not given the ID a tool needs, ask "
    "them for it instead of guessing. If the question is not about orders, "
    "customers or products, politely say you can only help with those. "
    "Never invent data that a tool did not return."
)


def ollama_chat(messages, tools=None):
    """Send messages (and optionally the toolbox menu) to Ollama; return its reply message."""
    body = {"model": MODEL, "messages": messages, "stream": False, "think": False}
    if tools:
        body["tools"] = tools
    request = urllib.request.Request(
        URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return json.loads(response.read().decode("utf-8"))["message"]


def answer_with_tools(user_prompt, chat_fn=ollama_chat):
    """Run the select -> execute -> final-answer flow. Returns a full transcript."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    # Step 1: show the model the toolbox and let it decide.
    first_reply = chat_fn(messages, TOOL_SCHEMAS)
    messages.append(first_reply)

    tools_called = []
    for call in first_reply.get("tool_calls") or []:
        name, arguments = parse_tool_call(call)  # safe even if the call is malformed

        # Step 2: WE run the tool (the model never runs anything itself).
        result = execute_tool(name, arguments)
        tools_called.append({"name": name, "arguments": arguments, "result": result})

        # Step 3: hand the result back to the model.
        messages.append({"role": "tool", "tool_name": name, "content": json.dumps(result)})

    if not tools_called:
        # The model answered directly (asked for an ID, or refused).
        final_answer = first_reply.get("content", "")
    else:
        # Step 4: ask for the final answer, using the tool results.
        final_answer = chat_fn(messages, None).get("content", "")

    return {
        "prompt": user_prompt,
        "tools_called": tools_called,
        "final_answer": final_answer,
        "messages": messages,
    }
