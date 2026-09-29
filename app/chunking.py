"""Turn the Day 6 knowledge-base markdown files into chunks (same rules as Day 6)."""

import re
from pathlib import Path

MAX_CHARS = 600


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
    """Pack whole sentences into chunks of at most max_chars, with 1-sentence overlap."""
    sentences = re.split(r"(?<=[.!?])\s+", body)
    chunks, current = [], []
    for sentence in sentences:
        if current and len(" ".join(current + [sentence])) > max_chars:
            chunks.append(" ".join(current))
            current = current[-1:] if len(current) > 1 else []
        current.append(sentence)
    if current:
        chunks.append(" ".join(current))
    return chunks


def load_chunks(kb_dir):
    """Read every .md file in kb_dir and return a flat list of chunk dicts."""
    kb_dir = Path(kb_dir)
    chunks = []
    for path in sorted(kb_dir.glob("*.md")):
        title, doc_id, sections = split_document(path.read_text())
        for heading, body in sections:
            for piece in chunk_text(body):
                chunks.append({
                    "doc_id": doc_id,
                    "section": heading,
                    "text": f"{title} > {heading}\n{piece}",
                })
    for index, chunk in enumerate(chunks):
        chunk["chunk_id"] = index
    return chunks
