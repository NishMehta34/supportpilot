"""Day 8: search the database for chunks similar to a question, scoped to one tenant.

Usage:
    python3 scripts/search_db.py "How long do I have to return something?"
    python3 scripts/search_db.py "How long do I have to return something?" --tenant acme
"""

import argparse
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import count_chunks, get_connection, search_chunks
from app.embeddings import get_embedding


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question")
    parser.add_argument("--tenant", default="nimbus")
    parser.add_argument("-k", type=int, default=5)
    args = parser.parse_args()

    try:
        query_vector = get_embedding(args.question)
    except urllib.error.URLError as error:
        print(f"Could not reach Ollama. Is it running? ({error})")
        sys.exit(1)

    with get_connection() as connection:
        cursor = connection.cursor()
        total = count_chunks(cursor, tenant_id=args.tenant)
        results = search_chunks(cursor, args.tenant, query_vector, k=args.k)

    print(f"Tenant '{args.tenant}' has {total} chunks stored.\n")
    print(f"Question: {args.question!r}\n")
    for rank, row in enumerate(results, start=1):
        print(f"{rank}. score={row['score']:.3f}  [{row['doc_id']}] {row['section']}")
        print(f"   {row['content'][:110]}...\n")


if __name__ == "__main__":
    main()
