"""Day 8: chunk, embed, and store the knowledge base in PostgreSQL + pgvector.

Usage:
    python3 scripts/ingest.py                        # ingest data/kb/ as tenant "nimbus"
    python3 scripts/ingest.py --tenant acme --kb-dir data/kb_other_tenant
"""

import argparse
import sys
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.chunking import load_chunks
from app.db import get_connection, replace_chunks, upsert_document
from app.embeddings import get_embeddings


def group_by_document(chunks):
    """The flat chunk list -> {doc_id: [chunks...]} so each document is upserted once."""
    grouped = {}
    for chunk in chunks:
        grouped.setdefault(chunk["doc_id"], []).append(chunk)
    return grouped


def ingest(kb_dir, tenant_id):
    chunks = load_chunks(kb_dir)
    if not chunks:
        print(f"No chunks found in {kb_dir}")
        return 0

    print(f"Loaded {len(chunks)} chunks from {kb_dir}")
    print("Generating embeddings (this talks to Ollama)...")
    try:
        vectors = get_embeddings([chunk["text"] for chunk in chunks])
    except urllib.error.URLError as error:
        print(f"Could not reach Ollama. Is it running? ({error})")
        sys.exit(1)
    for chunk, vector in zip(chunks, vectors):
        chunk["vector"] = vector

    grouped = group_by_document(chunks)
    with get_connection() as connection:
        cursor = connection.cursor()
        for doc_id, doc_chunks in grouped.items():
            title = doc_chunks[0]["text"].split(" > ")[0]
            document_id = upsert_document(
                cursor, tenant_id=tenant_id, doc_key=doc_id, title=title,
                source_path=str(kb_dir),
            )
            replace_chunks(cursor, document_id, tenant_id, doc_chunks)
            print(f"  {doc_id}: {len(doc_chunks)} chunks (tenant={tenant_id})")

    return len(chunks)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", default="nimbus")
    parser.add_argument("--kb-dir", default=str(Path(__file__).resolve().parent.parent / "data" / "kb"))
    args = parser.parse_args()

    total = ingest(Path(args.kb_dir), args.tenant)
    print(f"\nDone. {total} chunks stored for tenant '{args.tenant}'.")


if __name__ == "__main__":
    main()
