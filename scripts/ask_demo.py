"""Day 9: run a 20-question benchmark against the real /ask pipeline.

Requires: Ollama running, and the database ingested (Day 8).
Usage:
    python3 scripts/ask_demo.py
"""

import json
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.model_adapter import OllamaAdapter
from app.rag import ask_question
from app.retrieval import make_retriever

OUTPUT_FILE = Path(__file__).resolve().parent.parent / "artifacts" / "day09.json"
TENANT = "nimbus"

# 20 questions spanning all 5 documents, plus a few designed to be out of scope
# or ambiguous, since "not found" is a valid, correct outcome for those.
QUESTIONS = [
    "How long do I have to return an item if I'm a Gold member?",
    "Can I change my delivery address after my order has shipped?",
    "What's the warranty on the Nimbus Forge Mechanical Keyboard?",
    "How do I reset my password?",
    "My mouse cursor keeps stuttering, what can I do?",
    "Do you ship internationally?",
    "How much does express shipping cost?",
    "What happens if a package is lost?",
    "Can I return an item without the original packaging?",
    "How long does a refund take to show up?",
    "What is the return window for a Standard member?",
    "How do I claim a warranty replacement?",
    "Is there a restocking fee for opened electronics?",
    "How do I change my account email address?",
    "What payment methods do you accept?",
    "How do I pair the mouse over Bluetooth?",
    "What's the difference between Gold and Premium membership?",
    "I was charged twice for one order, what do I do?",
    "Can the USB-C hub charge my laptop?",
    "What's the weather like today?",  # deliberately out of scope
]


def main():
    retrieve = make_retriever()
    adapter = OllamaAdapter()
    chat_fn = lambda messages: adapter.chat(messages).get("content", "")

    results = []
    for question in QUESTIONS:
        try:
            result = ask_question(question, TENANT, retrieve, chat_fn)
        except urllib.error.URLError as error:
            print(f"Could not reach Ollama. Is it running? ({error})")
            sys.exit(1)

        acceptable = result["not_found"] or len(result["sources"]) > 0
        results.append({"question": question, **result, "acceptable": acceptable})

        tag = "NOT-FOUND" if result["not_found"] else f"{len(result['sources'])} source(s)"
        warn = f"  ⚠ invalid citations: {result['invalid_citations']}" if result["invalid_citations"] else ""
        print(f"[{tag:>12}] {question}{warn}")
        print(f"   {result['answer'][:140]}\n")

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(results, indent=2))

    acceptable_count = sum(r["acceptable"] for r in results)
    invalid_count = sum(bool(r["invalid_citations"]) for r in results)
    print("=" * 60)
    print(f"{acceptable_count}/{len(QUESTIONS)} either cited evidence or returned not-found")
    print(f"{invalid_count}/{len(QUESTIONS)} had a fabricated citation (should be 0)")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
