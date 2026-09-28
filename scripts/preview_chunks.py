"""Day 6: preview how the knowledge-base documents would be chunked. No AI needed.

Usage:
    python3 scripts/preview_chunks.py          # summary
    python3 scripts/preview_chunks.py show     # also print every chunk
"""

import re
import sys
from pathlib import Path

KB_DIR = Path(__file__).resolve().parent.parent / "data" / "kb"
MAX_CHARS = 600  # target maximum size of one chunk


def split_document(text):
    """Return (title, doc_id, [(section_heading, section_text), ...])."""
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip()
    match = re.search(r"Document ID:\s*(\S+)", text)
    doc_id = match.group(1) if match else "UNKNOWN"

    sections, heading, body = [], None, []
    for line in lines[1:]:
        if line.startswith("## "):
            if heading:
                sections.append((heading, " ".join(body).strip()))
            heading, body = line[3:].strip(), []
        elif heading and line.strip():
            body.append(line.strip())
    if heading:
        sections.append((heading, " ".join(body).strip()))
    return title, doc_id, sections


def chunk_text(body, max_chars=MAX_CHARS):
    """Pack whole sentences into chunks of at most max_chars, repeating 1 sentence as overlap."""
    sentences = re.split(r"(?<=[.!?])\s+", body)
    chunks, current = [], []
    for sentence in sentences:
        if current and len(" ".join(current + [sentence])) > max_chars:
            chunks.append(" ".join(current))
            current = current[-1:] if len(current) > 1 else []  # overlap
        current.append(sentence)
    if current:
        chunks.append(" ".join(current))
    return chunks


def main():
    show = "show" in sys.argv[1:]
    all_chunks = []

    for path in sorted(KB_DIR.glob("*.md")):
        title, doc_id, sections = split_document(path.read_text())
        count = 0
        for heading, body in sections:
            for piece in chunk_text(body):
                # Each chunk carries its title + section so it makes sense on its own.
                all_chunks.append(
                    {"doc_id": doc_id, "text": f"{title} > {heading}\n{piece}"}
                )
                count += 1
        print(f"{doc_id:<18} {len(sections):>2} sections -> {count:>2} chunks")

    sizes = [len(c["text"]) for c in all_chunks]
    print(f"\nTotal chunks: {len(all_chunks)}")
    print(f"Chunk size (characters): min {min(sizes)}, average {sum(sizes) // len(sizes)}, max {max(sizes)}")

    if show:
        for number, chunk in enumerate(all_chunks, start=1):
            print(f"\n--- chunk {number} [{chunk['doc_id']}] ---\n{chunk['text']}")


if __name__ == "__main__":
    main()
