-- Day 8: schema for storing chunks and their embeddings with tenant isolation.
-- Runs automatically the first time the Postgres container starts (see docker-compose.yml).

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id          SERIAL PRIMARY KEY,
    tenant_id   TEXT NOT NULL,
    doc_key     TEXT NOT NULL,          -- e.g. "KB-RETURNS", stable across re-ingestion
    title       TEXT NOT NULL,
    source_path TEXT NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, doc_key)
);

CREATE TABLE IF NOT EXISTS chunks (
    id           SERIAL PRIMARY KEY,
    document_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tenant_id    TEXT NOT NULL,         -- duplicated from documents so every query can filter here directly
    chunk_index  INTEGER NOT NULL,
    section      TEXT NOT NULL,
    content      TEXT NOT NULL,
    embedding    VECTOR(768) NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Every retrieval query filters by tenant_id first, so this index matters most.
CREATE INDEX IF NOT EXISTS idx_chunks_tenant ON chunks (tenant_id);

-- Approximate nearest-neighbor index for cosine distance. Fine to add now even
-- with only ~60 rows; it matters more as the table grows.
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
    ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);
