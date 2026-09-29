"""Day 7 part 1: embed 20 knowledge-base chunks (spread across all documents) and save them.

Usage:
    python3 scripts/embed_kb.py
"""

import json
import sys
import urllib.error
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunking import load_chunks
from app.embeddings import EMBED_MODEL, get_embeddings

KB_DIR = Path(__file__).resolve().parent.parent / "data" / "kb"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "artifacts" / "day07_embeddings.json"
NUMBER_TO_EMBED = 20


def pick_representative_sample(chunks, count):
    """Round-robin across documents, so every document gets a fair share instead
    of the first N chunks (which could all come from just one or two files).
    """
    by_doc = defaultdict(list)
    for chunk in chunks:
        by_doc[chunk["doc_id"]].append(chunk)

    sample, doc_ids = [], sorted(by_doc)
    while len(sample) < count and any(by_doc.values()):
        for doc_id in doc_ids:
            if by_doc[doc_id] and len(sample) < count:
                sample.append(by_doc[doc_id].pop(0))
    return sample


def main():
    all_chunks = load_chunks(KB_DIR)
    chunks = pick_representative_sample(all_chunks, NUMBER_TO_EMBED)

    from collections import Counter
    coverage = Counter(chunk["doc_id"] for chunk in chunks)
    print(f"Embedding {len(chunks)} chunks with '{EMBED_MODEL}'...")
    print(f"Coverage across documents: {dict(coverage)}")

    try:
        vectors = get_embeddings([chunk["text"] for chunk in chunks])
    except urllib.error.URLError as error:
        print(f"Could not reach Ollama. Is it running? ({error})")
        sys.exit(1)

    for chunk, vector in zip(chunks, vectors):
        chunk["vector"] = vector

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps({"model": EMBED_MODEL, "chunks": chunks}, indent=2))

    dims = len(vectors[0])
    print(f"Vector length: {dims} numbers per chunk")
    print(f"Saved {len(chunks)} embedded chunks to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
