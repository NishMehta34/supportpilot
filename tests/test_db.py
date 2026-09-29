"""Tests for the SQL layer, using an in-memory FAKE database (no Postgres needed).

The fake understands just enough SQL to prove our queries are shaped correctly:
tenant filtering, idempotent re-ingestion (delete-then-insert), and upsert-by-key.
"""

import re

from app.db import count_chunks, replace_chunks, search_chunks, to_vector_literal, upsert_document


class FakeCursor:
    """A tiny stand-in for a real database cursor, backed by Python lists."""

    def __init__(self, store):
        self.store = store  # shared dict: {"documents": [...], "chunks": [...]}
        self._last_result = []

    def execute(self, sql, params=()):
        sql = " ".join(sql.split())  # normalise whitespace for easy matching

        if sql.startswith("INSERT INTO documents"):
            tenant_id, doc_key, title, source_path = params
            existing = next(
                (d for d in self.store["documents"]
                 if d["tenant_id"] == tenant_id and d["doc_key"] == doc_key), None
            )
            if existing:
                existing.update(title=title, source_path=source_path)
                self._last_result = [(existing["id"],)]
            else:
                new_id = len(self.store["documents"]) + 1
                self.store["documents"].append(
                    {"id": new_id, "tenant_id": tenant_id, "doc_key": doc_key,
                     "title": title, "source_path": source_path}
                )
                self._last_result = [(new_id,)]

        elif sql.startswith("DELETE FROM chunks"):
            (document_id,) = params
            self.store["chunks"] = [c for c in self.store["chunks"] if c["document_id"] != document_id]

        elif sql.startswith("INSERT INTO chunks"):
            document_id, tenant_id, chunk_index, section, content, embedding = params
            self.store["chunks"].append({
                "id": len(self.store["chunks"]) + 1, "document_id": document_id,
                "tenant_id": tenant_id, "chunk_index": chunk_index, "section": section,
                "content": content, "embedding": embedding,
            })

        elif sql.startswith("SELECT c.id, c.section"):
            # search_chunks: filter by tenant, "rank" by a fake score derived from the vector text
            query_vector_literal, tenant_id, _query_vector_literal_again, k = params
            rows = [c for c in self.store["chunks"] if c["tenant_id"] == tenant_id]
            for row in rows:
                row["_score"] = _fake_similarity(row["embedding"], query_vector_literal)
            rows.sort(key=lambda r: r["_score"], reverse=True)
            doc_by_id = {d["id"]: d["doc_key"] for d in self.store["documents"]}
            self._last_result = [
                (r["id"], r["section"], r["content"], doc_by_id[r["document_id"]], r["_score"])
                for r in rows[:k]
            ]

        elif sql.startswith("SELECT COUNT(*) FROM chunks WHERE tenant_id"):
            (tenant_id,) = params
            self._last_result = [(sum(1 for c in self.store["chunks"] if c["tenant_id"] == tenant_id),)]

        elif sql.startswith("SELECT COUNT(*) FROM chunks"):
            self._last_result = [(len(self.store["chunks"]),)]

        else:
            raise AssertionError(f"FakeCursor does not understand this SQL: {sql!r}")

    def fetchone(self):
        return self._last_result[0]

    def fetchall(self):
        return self._last_result


def _fake_similarity(embedding_literal, query_literal):
    """A stand-in scorer: exact text match = 1.0, otherwise based on shared numbers."""
    if embedding_literal == query_literal:
        return 1.0
    a = set(re.findall(r"[-\d.]+", embedding_literal))
    b = set(re.findall(r"[-\d.]+", query_literal))
    return len(a & b) / max(len(a | b), 1)


def new_store():
    return {"documents": [], "chunks": []}


def chunk(section, text, vector):
    return {"section": section, "text": text, "vector": vector}


# ---------- to_vector_literal ----------
def test_vector_literal_format():
    assert to_vector_literal([0.1, 0.2, 0.3]) == "[0.1,0.2,0.3]"


def test_vector_literal_handles_integers():
    assert to_vector_literal([1, 2, 3]) == "[1.0,2.0,3.0]"


# ---------- upsert_document ----------
def test_upsert_document_creates_a_new_row():
    store = new_store()
    cursor = FakeCursor(store)
    doc_id = upsert_document(cursor, "nimbus", "KB-RETURNS", "Returns", "data/kb")
    assert doc_id == 1
    assert store["documents"][0]["doc_key"] == "KB-RETURNS"


def test_upsert_document_updates_instead_of_duplicating():
    store = new_store()
    cursor = FakeCursor(store)
    first_id = upsert_document(cursor, "nimbus", "KB-RETURNS", "Returns v1", "data/kb")
    second_id = upsert_document(cursor, "nimbus", "KB-RETURNS", "Returns v2", "data/kb")
    assert first_id == second_id
    assert len(store["documents"]) == 1
    assert store["documents"][0]["title"] == "Returns v2"


def test_same_doc_key_in_different_tenants_are_separate_rows():
    store = new_store()
    cursor = FakeCursor(store)
    upsert_document(cursor, "nimbus", "KB-FAQ", "Nimbus FAQ", "data/kb")
    upsert_document(cursor, "acme", "KB-FAQ", "Acme FAQ", "data/kb_other_tenant")
    assert len(store["documents"]) == 2


# ---------- replace_chunks: idempotent re-ingestion ----------
def test_replace_chunks_inserts_all_given_chunks():
    store = new_store()
    cursor = FakeCursor(store)
    chunks = [chunk("A", "text a", [1, 0]), chunk("B", "text b", [0, 1])]
    replace_chunks(cursor, document_id=1, tenant_id="nimbus", chunks_with_vectors=chunks)
    assert len(store["chunks"]) == 2


def test_re_ingesting_a_document_does_not_duplicate_chunks():
    store = new_store()
    cursor = FakeCursor(store)
    chunks = [chunk("A", "text a", [1, 0])]
    replace_chunks(cursor, document_id=1, tenant_id="nimbus", chunks_with_vectors=chunks)
    replace_chunks(cursor, document_id=1, tenant_id="nimbus", chunks_with_vectors=chunks)
    assert len(store["chunks"]) == 1  # not 2


def test_re_ingesting_with_fewer_chunks_drops_the_extra_old_ones():
    store = new_store()
    cursor = FakeCursor(store)
    old = [chunk("A", "a", [1, 0]), chunk("B", "b", [0, 1]), chunk("C", "c", [1, 1])]
    replace_chunks(cursor, document_id=1, tenant_id="nimbus", chunks_with_vectors=old)
    new = [chunk("A", "a-updated", [1, 0])]
    replace_chunks(cursor, document_id=1, tenant_id="nimbus", chunks_with_vectors=new)
    assert len(store["chunks"]) == 1
    assert store["chunks"][0]["content"] == "a-updated"


def test_replacing_one_document_does_not_touch_another():
    store = new_store()
    cursor = FakeCursor(store)
    replace_chunks(cursor, document_id=1, tenant_id="nimbus", chunks_with_vectors=[chunk("A", "a", [1, 0])])
    replace_chunks(cursor, document_id=2, tenant_id="nimbus", chunks_with_vectors=[chunk("B", "b", [0, 1])])
    replace_chunks(cursor, document_id=1, tenant_id="nimbus", chunks_with_vectors=[chunk("A2", "a2", [1, 1])])
    assert len(store["chunks"]) == 2
    assert any(c["section"] == "B" for c in store["chunks"])


# ---------- search_chunks: the multitenancy test the plan requires ----------
def _seed_two_tenants(store):
    cursor = FakeCursor(store)
    nimbus_doc = upsert_document(cursor, "nimbus", "KB-RETURNS", "Nimbus Returns", "data/kb")
    replace_chunks(cursor, nimbus_doc, "nimbus", [chunk("Window", "Nimbus: 30 days", [1, 0, 0])])
    acme_doc = upsert_document(cursor, "acme", "KB-FAQ", "Acme FAQ", "data/kb_other_tenant")
    replace_chunks(cursor, acme_doc, "acme", [chunk("Window", "Acme: 14 days", [1, 0, 0])])
    return cursor


def test_search_only_returns_the_requesting_tenants_chunks():
    store = new_store()
    cursor = _seed_two_tenants(store)
    results = search_chunks(cursor, "nimbus", [1, 0, 0], k=5)
    assert len(results) == 1
    assert results[0]["doc_id"] == "KB-RETURNS"
    assert "Nimbus" in results[0]["content"]


def test_search_never_leaks_another_tenants_chunks_even_with_identical_vectors():
    store = new_store()
    cursor = _seed_two_tenants(store)
    # Both tenants have an identical-looking chunk vector [1,0,0]. Asking as "acme"
    # must never return nimbus's row, even though it would score perfectly.
    results = search_chunks(cursor, "acme", [1, 0, 0], k=5)
    assert all(r["doc_id"] != "KB-RETURNS" or "Acme" in r["content"] for r in results)
    assert all("Nimbus" not in r["content"] for r in results)


def test_search_respects_the_k_limit():
    store = new_store()
    cursor = FakeCursor(store)
    doc_id = upsert_document(cursor, "nimbus", "KB-X", "X", "data/kb")
    many = [chunk(f"S{i}", f"text {i}", [1, 0]) for i in range(10)]
    replace_chunks(cursor, doc_id, "nimbus", many)
    assert len(search_chunks(cursor, "nimbus", [1, 0], k=3)) == 3


# ---------- count_chunks ----------
def test_count_chunks_total_and_per_tenant():
    store = new_store()
    cursor = _seed_two_tenants(store)
    assert count_chunks(cursor) == 2
    assert count_chunks(cursor, tenant_id="nimbus") == 1
    assert count_chunks(cursor, tenant_id="acme") == 1
