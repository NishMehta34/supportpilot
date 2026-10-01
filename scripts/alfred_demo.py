"""Day 11: Alfred, re-implemented on OUR OWN agent loop (no smolagents, no framework).

This is the Hugging Face Agents Course's butler exercise, rebuilt from scratch
on the exact same bounded think-act-observe loop from Day 4.

Usage:
    python3 scripts/alfred_demo.py
"""

import json
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent_loop import run_agent, save_trace
from app.alfred_tools import ALFRED_TOOL_SCHEMAS, execute_alfred_tool

ARTIFACTS = Path(__file__).resolve().parent.parent / "artifacts" / "day11_traces"

TASKS = [
    "Check the weather in Gotham, and suggest a playlist that would suit it.",
    "Selina Kyle is on the guest list. What's her relation to the host, and does the menu need to account for anything about her?",
    "Suggest an Italian menu and tell me if it will work for any guest with dietary restrictions, given what you know about the guest list.",
]


def main():
    for number, task in enumerate(TASKS, start=1):
        print(f"\n--- Task {number}: {task}")
        try:
            result = run_agent(
                task,
                tool_schemas=ALFRED_TOOL_SCHEMAS,
                execute_tool=execute_alfred_tool,
            )
        except urllib.error.URLError as error:
            print(f"Could not reach Ollama. Is it running? ({error})")
            sys.exit(1)

        save_trace(result, ARTIFACTS / f"task_{number}.json")
        tools_used = [step["tool"] for step in result["trace"] if step["type"] == "tool_call"]
        print(f"stop_reason={result['stop_reason']}  steps={result['steps_used']}  tools={tools_used}")
        print(f"Answer: {result['final_answer']}")

    print(f"\nTraces saved in {ARTIFACTS}")


if __name__ == "__main__":
    main()
