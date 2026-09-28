"""Day 2: classify 10 support messages and save the results."""

import json
import sys
import urllib.error
from pathlib import Path

from app.classifier import MODEL, ClassificationError, classify_message

MESSAGES = [
    "I was charged twice for my subscription this month!",
    "The app crashes every time I open the settings page.",
    "My package was supposed to arrive last week and still hasn't.",
    "I can't log in, it says my password is wrong but I just reset it.",
    "How do I change the email address on my account?",
    "URGENT: my whole team is locked out and we have a demo in an hour!",
    "Can I get a refund for an order I cancelled?",
    "The tracking link you sent me shows an error.",
    "I just wanted to say thanks, your service is great.",
    "Your invoice shows the wrong company name.",
]

OUTPUT_FILE = Path(__file__).resolve().parent.parent / "artifacts" / "day02.json"


def main():
    results = []
    for message in MESSAGES:
        try:
            classification = classify_message(message)
            results.append(
                {"message": message, "classification": classification.model_dump()}
            )
            print(f"OK       {message[:50]!r} -> {classification.category}/{classification.priority}")
        except ClassificationError as error:
            results.append({"message": message, "classification": None, "error": str(error)})
            print(f"REJECTED {message[:50]!r}")
        except urllib.error.URLError as error:
            print(f"Could not reach Ollama. Is it running? ({error})")
            sys.exit(1)

    valid = sum(1 for r in results if r["classification"] is not None)
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps({"model": MODEL, "results": results}, indent=2))
    print(f"\n{valid}/{len(MESSAGES)} valid. Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
