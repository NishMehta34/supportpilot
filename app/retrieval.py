"""Wires app.rag's retrieve_fn to the real database and embedding model.

Kept as a separate, thin file so app/rag.py never has to know about Postgres
or Ollama, and so tests can swap this whole file out for a fake.
"""

from app.db import get_connection, search_chunks
from app.embeddings import get_embedding


def make_retriever():
    """Return a retrieve_fn(question, tenant_id, k) that hits the real DB + model."""

    def retrieve(question, tenant_id, k):
        query_vector = get_embedding(question)
        with get_connection() as connection:
            cursor = connection.cursor()
            return search_chunks(cursor, tenant_id, query_vector, k=k)

    return retrieve
