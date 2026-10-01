"""Day 12, version 1: the 2-tool agent on YOUR raw loop from Day 4/11, with
exactly 2 tools (get_order, get_customer) to match the smolagents and
mini_agent versions for a fair comparison.

Usage:
    python3 scripts/raw_version.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent_loop import run_agent
from app.tools import TOOL_FUNCTIONS

# Every schema and the execute function are hand-written, by us, in full.
# Compare the line count and detail here against smolagents_version.py.
TWO_TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "get_order",
        "description": "Look up an order's status and delivery date by order ID.",
        "parameters": {"type": "object",
                       "properties": {"order_id": {"type": "string", "description": "e.g. ORD-1001"}},
                       "required": ["order_id"]}}},
    {"type": "function", "function": {
        "name": "get_customer",
        "description": "Look up a customer's name, email and tier by customer ID.",
        "parameters": {"type": "object",
                       "properties": {"customer_id": {"type": "string", "description": "e.g. CUS-001"}},
                       "required": ["customer_id"]}}},
]


def execute_two_tools(name, arguments):
    function = TOOL_FUNCTIONS.get(name)
    if function is None or name not in ("get_order", "get_customer"):
        return {"error": f"Unknown tool: {name}"}
    try:
        return function(**arguments)
    except TypeError as error:
        return {"error": f"Invalid arguments for {name}: {error}"}


TASKS = [
    "Where is order ORD-1001, and who is the customer who placed it?",
    "What's the status of order ORD-1002?",
]


def main():
    for task in TASKS:
        print(f"\n--- Task: {task}")
        result = run_agent(task, tool_schemas=TWO_TOOL_SCHEMAS, execute_tool=execute_two_tools)
        print(f"Answer: {result['final_answer']}")
        print(f"(stop_reason={result['stop_reason']}, steps={result['steps_used']})")


if __name__ == "__main__":
    main()
