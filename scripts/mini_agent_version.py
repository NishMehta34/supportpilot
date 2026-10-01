"""Day 12, version 3: the SAME 2-tool agent on our own tiny MiniAgent wrapper.

Usage:
    python3 scripts/mini_agent_version.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.mini_agent import MiniAgent
from app.tool_loop import ollama_chat
from raw_version import TWO_TOOL_SCHEMAS, execute_two_tools

TASKS = [
    "Where is order ORD-1001, and who is the customer who placed it?",
    "What's the status of order ORD-1002?",
]


def main():
    agent = MiniAgent(chat_fn=ollama_chat, tools=TWO_TOOL_SCHEMAS, execute_tool=execute_two_tools)
    for task in TASKS:
        print(f"\n--- Task: {task}")
        answer = agent.run(task)
        print(f"Answer: {answer}")
        print(agent.explain_last_run())


if __name__ == "__main__":
    main()
