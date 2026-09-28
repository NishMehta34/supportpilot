"""Day 4: run 5 multi-step tasks, save a trace for each, and check the limits held."""

import json
import sys
import urllib.error
from pathlib import Path

from app.agent_loop import MAX_STEPS, run_agent, save_trace
from app.tool_loop import MODEL

# (task, text the correct final answer must contain)
TASKS = [
    ("Find all orders for customer CUS-001, then tell me the total price of the products in those orders.", "70.49"),
    ("What is the name of the customer who placed order ORD-1002, and what product did they buy?", "Ben Carter"),
    ("How much would 3 units of the product in order ORD-1001 cost?", "74.97"),
    ("Which orders are currently processing, and who are the customers?", "Ben Carter"),
    ("Compare the price of the products in ORD-1001 and ORD-1002. Which is cheaper and by how much?", "64.01"),
]

ROOT = Path(__file__).resolve().parent.parent
TRACE_DIR = ROOT / "artifacts" / "traces"
OUTPUT_FILE = ROOT / "artifacts" / "day04.json"


def main():
    summaries = []
    correct = 0
    within_limit = 0

    for number, (task, expected_text) in enumerate(TASKS, start=1):
        try:
            run = run_agent(task)
        except urllib.error.URLError as error:
            print(f"Could not reach Ollama. Is it running? ({error})")
            sys.exit(1)

        trace_path = save_trace(run, TRACE_DIR / f"day04_task{number:02d}.json")
        tools_used = [c["name"] for s in run["steps"] for c in s["tool_calls"]]
        ok = expected_text in run["final_answer"]
        in_limit = run["steps_used"] <= MAX_STEPS
        correct += ok
        within_limit += in_limit

        print(f"Task {number}: {'PASS' if ok else 'CHECK'}  stop={run['stop_reason']}  "
              f"steps={run['steps_used']}/{MAX_STEPS}")
        print(f"   tools: {tools_used}")
        print(f"   answer: {run['final_answer'][:120]!r}")
        print(f"   trace: {trace_path.name}\n")

        summaries.append({
            "task": task, "expected_text": expected_text, "answer_correct": ok,
            "stop_reason": run["stop_reason"], "steps_used": run["steps_used"],
            "tools_used": tools_used, "final_answer": run["final_answer"],
            "trace_file": str(trace_path.relative_to(ROOT)),
        })

    OUTPUT_FILE.write_text(json.dumps({"model": MODEL, "max_steps": MAX_STEPS, "runs": summaries}, indent=2))
    print(f"Terminated within limit: {within_limit}/{len(TASKS)}")
    print(f"Correct answers: {correct}/{len(TASKS)}")
    print(f"Saved summary to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
