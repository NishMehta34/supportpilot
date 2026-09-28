"""Day 3: run 10 prompts through the tool loop and check the right tool was chosen."""

import json
import sys
import urllib.error
from pathlib import Path

from app.tool_loop import MODEL, answer_with_tools

# (prompt, expected tool name, or None if the AI should ask for info / refuse)
CASES = [
    ("Where is my order ORD-1001?", "get_order"),
    ("What's the status of ORD-1002?", "get_order"),
    ("Look up customer CUS-001 for me.", "get_customer"),
    ("What email do we have for customer CUS-002?", "get_customer"),
    ("How much does product PRD-001 cost?", "get_product"),
    ("Is PRD-003 in stock?", "get_product"),
    ("Who is customer CUS-003 and what tier are they?", "get_customer"),
    ("Tell me about order ORD-9999.", "get_order"),  # not found: must be handled gracefully
    ("Where is my order?", None),  # no ID given: should ask for it
    ("What's the weather in Paris?", None),  # off-topic: should politely refuse
]

OUTPUT_FILE = Path(__file__).resolve().parent.parent / "artifacts" / "day03.json"


def main():
    runs = []
    correct = 0
    for prompt, expected in CASES:
        try:
            run = answer_with_tools(prompt)
        except urllib.error.URLError as error:
            print(f"Could not reach Ollama. Is it running? ({error})")
            sys.exit(1)

        chosen = [call["name"] for call in run["tools_called"]]
        ok = (chosen == [expected]) if expected else (chosen == [])
        correct += ok
        run["expected_tool"] = expected
        run["correct"] = ok
        runs.append(run)
        print(f"{'PASS' if ok else 'FAIL'}  {prompt!r}  expected={expected} got={chosen}")
        print(f"      answer: {run['final_answer'][:100]!r}\n")

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps({"model": MODEL, "runs": runs}, indent=2))
    print(f"{correct}/{len(CASES)} correct. Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
