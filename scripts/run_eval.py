"""Day 10: run the 30-case benchmark against the real pipeline and score it.

Requires: Ollama running, the database ingested (Day 8), tenant 'nimbus'.
Usage:
    python3 scripts/run_eval.py
"""

import json
import sys
import time
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.eval_scoring import load_cases, score_case, summarize
from app.model_adapter import OllamaAdapter
from app.rag import ask_question
from app.retrieval import make_retriever

CASES_FILE = Path(__file__).resolve().parent.parent / "evals" / "rag_cases.jsonl"
SCORECARD_FILE = Path(__file__).resolve().parent.parent / "artifacts" / "day10_scorecard.json"


def main():
    cases = load_cases(CASES_FILE)
    retrieve = make_retriever()
    adapter = OllamaAdapter()
    chat_fn = lambda messages: adapter.chat(messages).get("content", "")

    entries = []
    for case in cases:
        try:
            retrieved_chunks = retrieve(case["question"], case["tenant_id"], 5)
        except urllib.error.URLError as error:
            print(f"Could not reach Ollama. Is it running? ({error})")
            sys.exit(1)

        started = time.perf_counter()
        result = ask_question(case["question"], case["tenant_id"], retrieve, chat_fn)
        elapsed_ms = round((time.perf_counter() - started) * 1000, 1)

        entry = score_case(case, retrieved_chunks, result, elapsed_ms)
        entries.append(entry)

        if entry["scored"]:
            mark = "PASS" if entry["correct"] else "FAIL"
        else:
            mark = "LOG "
        print(f"[{mark}] {case['id']:<4} {case['category']:<15} {case['question'][:60]}")
        if entry["reasons"]:
            for reason in entry["reasons"]:
                print(f"       -> {reason}")

    summary = summarize(entries)

    print("\n" + "=" * 70)
    print(f"Total cases:         {summary['total_cases']}")
    print(f"Auto-scored cases:   {summary['auto_scored_cases']}")
    print(f"Answer correctness:  {summary['answer_correctness']}")
    print(f"Retrieval hit@5:     {summary['hit_at_k']}")
    print(f"Citation rate:       {summary['citation_rate']}")
    print(f"Fabricated citations:{summary['fabricated_citations']}")
    print(f"Latency (ms):        avg={summary['latency_ms']['avg']}  "
          f"median={summary['latency_ms']['median']}  p95={summary['latency_ms']['p95']}")
    print(f"\n{len(summary['failures'])} auto-scored failure(s). See artifacts/day10_scorecard.json for detail.")

    SCORECARD_FILE.parent.mkdir(exist_ok=True)
    SCORECARD_FILE.write_text(json.dumps({"summary": summary, "entries": entries}, indent=2))
    print(f"Saved full scorecard to {SCORECARD_FILE}")


if __name__ == "__main__":
    main()
