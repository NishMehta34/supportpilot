"""Tests for the RAG pipeline logic. No real model, database, or network needed."""

from app.rag import (
    NOT_FOUND_MESSAGE,
    SIMILARITY_THRESHOLD,
    assemble_context,
    ask_question,
    extract_citations,
    validate_citations,
)


def make_chunk(doc_id, section, content, score):
    return {"doc_id": doc_id, "section": section, "content": content, "score": score}


# ---------- assemble_context ----------
def test_context_labels_chunks_in_order():
    chunks = [make_chunk("KB-A", "Sec1", "text1", 0.9), make_chunk("KB-B", "Sec2", "text2", 0.8)]
    context, sources = assemble_context(chunks)
    assert "[S1]" in context and "[S2]" in context
    assert sources[0]["source_id"] == "S1" and sources[1]["source_id"] == "S2"


def test_context_includes_doc_and_section_for_orientation():
    context, _ = assemble_context([make_chunk("KB-RETURNS", "Return window", "30 days", 0.9)])
    assert "KB-RETURNS" in context and "Return window" in context


def test_context_snippet_is_truncated_not_the_full_chunk():
    long_text = "x" * 500
    _, sources = assemble_context([make_chunk("KB-A", "S", long_text, 0.9)])
    assert len(sources[0]["snippet"]) <= 200


# ---------- extract_citations / validate_citations ----------
def test_extract_citations_finds_all_tags():
    assert extract_citations("Fact one [S1]. Fact two [S3].") == ["1", "3"]


def test_extract_citations_returns_empty_list_when_none():
    assert extract_citations("No citations here.") == []


def test_validate_citations_accepts_real_sources():
    sources = [{"source_id": "S1"}, {"source_id": "S2"}]
    assert validate_citations("Fact [S1] and fact [S2].", sources) == []


def test_validate_citations_catches_a_fabricated_source():
    sources = [{"source_id": "S1"}]
    assert validate_citations("Fact [S1], also [S7].", sources) == ["S7"]


def test_validate_citations_handles_no_citations_at_all():
    assert validate_citations("plain answer", [{"source_id": "S1"}]) == []


# ---------- ask_question: the full pipeline with fakes ----------
def fake_retrieve(chunks):
    return lambda question, tenant_id, k: chunks[:k]


def test_low_similarity_returns_not_found_without_calling_the_model():
    calls = []
    retrieve = fake_retrieve([make_chunk("KB-A", "S", "text", SIMILARITY_THRESHOLD - 0.1)])
    result = ask_question("q", "nimbus", retrieve, chat_fn=lambda m: calls.append(m) or "should not run")
    assert result["not_found"] is True
    assert result["sources"] == []
    assert calls == []  # the model was never even called - saves time and cost


def test_empty_retrieval_returns_not_found():
    result = ask_question("q", "nimbus", fake_retrieve([]), chat_fn=lambda m: "unused")
    assert result["not_found"] is True


def test_good_evidence_produces_a_cited_answer():
    chunks = [make_chunk("KB-RETURNS", "Return window", "30 days for Standard.", 0.8)]
    retrieve = fake_retrieve(chunks)
    answer = "You have 30 days to return an item [S1]."
    result = ask_question("How long to return?", "nimbus", retrieve, chat_fn=lambda m: answer)
    assert result["not_found"] is False
    assert len(result["sources"]) == 1
    assert result["sources"][0]["doc_id"] == "KB-RETURNS"
    assert result["invalid_citations"] == []


def test_model_saying_not_found_is_respected_even_with_good_evidence():
    # Retrieval found something above the threshold, but the model itself decides
    # the evidence doesn't actually answer the question.
    chunks = [make_chunk("KB-A", "S", "unrelated but similar-sounding text", 0.9)]
    retrieve = fake_retrieve(chunks)
    result = ask_question("q", "nimbus", retrieve, chat_fn=lambda m: NOT_FOUND_MESSAGE)
    assert result["not_found"] is True
    assert result["sources"] == []


def test_fabricated_citation_is_flagged_not_silently_trusted():
    chunks = [make_chunk("KB-A", "S", "real content", 0.8)]
    retrieve = fake_retrieve(chunks)
    answer = "Real fact [S1]. Made up fact [S9]."
    result = ask_question("q", "nimbus", retrieve, chat_fn=lambda m: answer)
    assert result["invalid_citations"] == ["S9"]


def test_only_actually_cited_sources_are_returned_not_every_retrieved_chunk():
    chunks = [
        make_chunk("KB-A", "S1sec", "content one", 0.9),
        make_chunk("KB-B", "S2sec", "content two", 0.8),
    ]
    retrieve = fake_retrieve(chunks)
    answer = "Only used the first fact [S1]."  # never cites S2
    result = ask_question("q", "nimbus", retrieve, chat_fn=lambda m: answer)
    assert [s["source_id"] for s in result["sources"]] == ["S1"]


def test_k_is_passed_through_to_retrieval():
    seen = {}

    def retrieve(question, tenant_id, k):
        seen["k"] = k
        return [make_chunk("KB-A", "S", "c", 0.9)]

    ask_question("q", "nimbus", retrieve, chat_fn=lambda m: "answer [S1]", k=3)
    assert seen["k"] == 3


def test_tenant_id_is_passed_through_to_retrieval():
    seen = {}

    def retrieve(question, tenant_id, k):
        seen["tenant_id"] = tenant_id
        return [make_chunk("KB-A", "S", "c", 0.9)]

    ask_question("q", "acme", retrieve, chat_fn=lambda m: "answer [S1]")
    assert seen["tenant_id"] == "acme"
