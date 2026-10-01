"""Day 12, version 2: the SAME 2-tool agent built on smolagents, a real framework.

Compare this against app/agent_loop.py (version 1, your raw loop) and
app/mini_agent.py (version 3, your own tiny wrapper).

Setup (one-time):
    pip install "smolagents[litellm]"

Usage:
    python3 scripts/smolagents_version.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from smolagents import LiteLLMModel, ToolCallingAgent, tool

from app.tools import get_customer, get_order

# --- Same 2 tools as the comparison, now as smolagents @tool functions. ---
# Notice: no hand-written JSON schema. smolagents reads the type hints and
# docstring below and builds the schema for us. That's the convenience Day 11
# talked about: less code, but also less visible.


@tool
def get_order_tool(order_id: str) -> dict:
    """Look up an order's status and delivery date by order ID.

    Args:
        order_id: The order ID, like ORD-1001
    """
    return get_order(order_id)


@tool
def get_customer_tool(customer_id: str) -> dict:
    """Look up a customer's name, email and tier by customer ID.

    Args:
        customer_id: The customer ID, like CUS-001
    """
    return get_customer(customer_id)


def build_agent(model_id="ollama_chat/qwen3", api_base="http://localhost:11434"):
    model = LiteLLMModel(model_id=model_id, api_base=api_base, num_ctx=8192)
    return ToolCallingAgent(tools=[get_order_tool, get_customer_tool], model=model, max_steps=6)


TASKS = [
    "Where is order ORD-1001, and who is the customer who placed it?",
    "What's the status of order ORD-1002?",
]


def main():
    agent = build_agent()
    for task in TASKS:
        print(f"\n--- Task: {task}")
        answer = agent.run(task)
        print(f"Answer: {answer}")


if __name__ == "__main__":
    main()
