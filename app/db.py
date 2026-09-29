"""Talk to PostgreSQL + pgvector: store chunks, and search them by similarity,
always scoped to a tenant.
"""

import os
from contextlib import contextmanager

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://supportpilot:supportpilot@localhost:5432/supportpilot"
)


def _real_connect(database_url):
    import psycopg  # imported lazily so tests never need it installed
    return psycopg.connect(database_url)


@contextmanager
def get_connection(database_url=DATABASE_URL, connect=_real_connect):
    """A connection that commits on success and rolls back on error."""
    connection = connect(database_url)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def to_vector_literal(vector):
    """Python list -> the text format pgvector expects, e.g. '[0.1,0.2,0.3]'."""
    return "[" + ",".join(repr(float(x)) for x in vector) + "]"


def upsert_document(cursor, tenant_id, doc_key, title, source_path):
    """Insert a document, or update it if (tenant_id, doc_key) already exists. Returns its id."""
    cursor.execute(
        """
        INSERT INTO documents (tenant_id, doc_key, title, source_path, updated_at)
        VALUES (%s, %s, %s, %s, now())
        ON CONFLICT (tenant_id, doc_key)
        DO UPDATE SET title = EXCLUDED.title,
                      source_path = EXCLUDED.source_path,
                      updated_at = now()
        RETURNING id
        """,
        (tenant_id, doc_key, title, source_path),
    )
    return cursor.fetchone()[0]


def replace_chunks(cursor, document_id, tenant_id, chunks_with_vectors):
    """Delete a document's old chunks and insert the new ones.

    This makes ingestion repeatable: re-running it on a changed document never
    leaves stale or duplicate chunks behind.
    """
    cursor.execute("DELETE FROM chunks WHERE document_id = %s", (document_id,))
    for index, chunk in enumerate(chunks_with_vectors):
        cursor.execute(
            """
            INSERT INTO chunks (document_id, tenant_id, chunk_index, section, content, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                document_id, tenant_id, index, chunk["section"], chunk["text"],
                to_vector_literal(chunk["vector"]),
            ),
        )


def search_chunks(cursor, tenant_id, query_vector, k=5):
    """Return the k chunks most similar to query_vector, restricted to one tenant.

    '<=>' is pgvector's cosine DISTANCE operator: 0 = identical, 2 = opposite.
    We convert it to a similarity score (1 - distance) so higher is always better,
    matching the cosine_similarity() used in app/embeddings.py.
    """
    cursor.execute(
        """
        SELECT c.id, c.section, c.content, d.doc_key,
               1 - (c.embedding <=> %s) AS score
        FROM chunks AS c
        JOIN documents AS d ON d.id = c.document_id
        WHERE c.tenant_id = %s
        ORDER BY c.embedding <=> %s
        LIMIT %s
        """,
        (to_vector_literal(query_vector), tenant_id, to_vector_literal(query_vector), k),
    )
    columns = ["chunk_id", "section", "content", "doc_id", "score"]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def count_chunks(cursor, tenant_id=None):
    if tenant_id:
        cursor.execute("SELECT COUNT(*) FROM chunks WHERE tenant_id = %s", (tenant_id,))
    else:
        cursor.execute("SELECT COUNT(*) FROM chunks")
    return cursor.fetchone()[0]
