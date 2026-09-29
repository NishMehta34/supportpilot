"""Day 7 part 2: embed 5+ test queries and find their closest chunks.

Usage:
    python3 scripts/similarity_demo.py
"""

import json
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.embeddings import cosine_similarity, get_embedding, top_k

EMBEDDINGS_FILE = Path(__file__).resolve().parent.parent / "artifacts" / "day07_embeddings.json"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "artifacts" / "day07_notes.json"

# (query, expected doc_id of a genuinely related chunk)
RELATED_QUERIES = [
    ("How long do I have to return something?", "KB-RETURNS"),
    ("My package tracking hasn't updated in a while", "KB-SHIPPING"),
    ("The keyboard has keys that don't work anymore", "KB-WARRANTY"),
    ("I forgot my password and can't log in", "KB-ACCOUNT"),
    ("The mouse cursor keeps stuttering", "KB-TROUBLESHOOT"),
]

# A query that should NOT match anything well, to see what an unrelated score looks like.
UNRELATED_QUERY = "What is the capital of France?"


def main():
    if not EMBEDDINGS_FILE.exists():
        print(f"Missing {EMBEDDINGS_FILE}. Run scripts/embed_kb.py first.")
        sys.exit(1)

    data = json.loads(EMBEDDINGS_FILE.read_text())
    chunks = data["chunks"]
    print(f"Loaded {len(chunks)} embedded chunks (model: {data['model']})\n")

    results = []
    for query, expected_doc in RELATED_QUERIES + [(UNRELATED_QUERY, None)]:
        try:
            query_vector = get_embedding(query)
        except urllib.error.URLError as error:
            print(f"Could not reach Ollama. Is it running? ({error})")
            sys.exit(1)

        matches = top_k(query_vector, chunks, k=5)
        top_match = matches[0]
        found_expected = expected_doc is not None and any(m["doc_id"] == expected_doc for m in matches)

        label = "RELATED  " if expected_doc else "UNRELATED"
        print(f"{label} query: {query!r}")
        for rank, match in enumerate(matches, start=1):
            marker = " <-- expected doc" if match["doc_id"] == expected_doc else ""
            print(f"   {rank}. score={match['score']:.3f}  [{match['doc_id']}] {match['section']}{marker}")
        print()

        results.append({
            "query": query, "expected_doc": expected_doc,
            "top_score": top_match["score"], "top_doc": top_match["doc_id"],
            "found_expected_in_top5": found_expected, "matches": matches,
        })

    related_scores = [r["top_score"] for r in results if r["expected_doc"]]
    unrelated_score = results[-1]["top_score"]
    hits = sum(r["found_expected_in_top5"] for r in results if r["expected_doc"])

    print("=" * 60)
    print(f"Related queries: {hits}/{len(related_scores)} found the expected document in the top 5")
    print(f"Average top score for related queries:   {sum(related_scores)/len(related_scores):.3f}")
    print(f"Top score for the unrelated query:        {unrelated_score:.3f}")
    print("A healthy embedding model scores related queries noticeably higher than unrelated ones.")

    OUTPUT_FILE.write_text(json.dumps(results, indent=2))
    print(f"\nSaved full results to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
