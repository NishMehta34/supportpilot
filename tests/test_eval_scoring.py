"""Tests for the Day 10 scoring logic. No real model, database, or JSONL file needed."""

from app.eval_scoring import contains_match, hit_at_k, score_case, summarize

NOT_FOUND = "I couldn't find that in our knowledge base."


def chunk(doc_id):
    return {"doc_id": doc_id}


def result(answer="", sources=None, not_found=False, invalid_citations=None):
    return {"answer": answer, "sources": sources or [], "not_found": not_found,
            "invalid_citations": invalid_citations or []}


# ---------- hit_at_k ----------
def test_hit_when_expected_doc_is_retrieved():
    assert hit_at_k(["KB-A"], [chunk("KB-B"), chunk("KB-A")]) is True


def test_miss_when_expected_doc_is_not_retrieved():
    assert hit_at_k(["KB-A"], [chunk("KB-B"), chunk("KB-C")]) is False


def test_hit_with_multiple_expected_docs_needs_only_one():
    assert hit_at_k(["KB-A", "KB-B"], [chunk("KB-C"), chunk("KB-B")]) is True


def test_not_applicable_when_no_expected_docs():
    assert hit_at_k([], [chunk("KB-A")]) is None


# ---------- contains_match ----------
def test_all_present_when_every_substring_found():
    all_present, any_present, matched, missing = contains_match("You get 45 days free express.", ["45", "express"])
    assert all_present and any_present and missing == []


def test_partial_match_is_not_all_present():
    all_present, any_present, matched, missing = contains_match("You get 45 days.", ["45", "express"])
    assert not all_present and any_present
    assert missing == ["express"]


def test_match_is_case_insensitive():
    assert contains_match("FREE EXPRESS SHIPPING", ["express"])[0] is True


# ---------- score_case: easy / multi_document ----------
def test_easy_case_correct_when_fact_present_and_doc_retrieved():
    case = {"id": "E1", "category": "easy", "question": "q",
            "expected_doc_ids": ["KB-RETURNS"], "expected_contains": ["30 days"]}
    entry = score_case(case, [chunk("KB-RETURNS")], result("You have 30 days.", sources=[{}]), 120)
    assert entry["correct"] is True
    assert entry["hit_at_k"] is True


def test_easy_case_wrong_when_fact_missing():
    case = {"id": "E2", "category": "easy", "question": "q",
            "expected_doc_ids": ["KB-RETURNS"], "expected_contains": ["30 days"]}
    entry = score_case(case, [chunk("KB-RETURNS")], result("You have some days.", sources=[{}]), 100)
    assert entry["correct"] is False
    assert "missing expected fact" in entry["reasons"][0]


def test_easy_case_wrong_when_it_incorrectly_says_not_found():
    case = {"id": "E3", "category": "easy", "question": "q",
            "expected_doc_ids": ["KB-RETURNS"], "expected_contains": ["30 days"]}
    entry = score_case(case, [chunk("KB-RETURNS")], result(NOT_FOUND, not_found=True), 90)
    assert entry["correct"] is False


def test_multi_document_still_scores_on_contains_match():
    case = {"id": "M1", "category": "multi_document", "question": "q",
            "expected_doc_ids": ["KB-A", "KB-B"], "expected_contains": ["45"]}
    entry = score_case(case, [chunk("KB-A"), chunk("KB-B")], result("45 days [S1][S2].", sources=[{}, {}]), 200)
    assert entry["correct"] is True


# ---------- score_case: out_of_scope / adversarial ----------
def test_out_of_scope_correct_when_not_found_as_expected():
    case = {"id": "O1", "category": "out_of_scope", "question": "q", "expected_not_found": True}
    entry = score_case(case, [], result(NOT_FOUND, not_found=True), 50)
    assert entry["correct"] is True


def test_out_of_scope_wrong_when_it_confidently_answers_instead():
    case = {"id": "O2", "category": "out_of_scope", "question": "q", "expected_not_found": True}
    entry = score_case(case, [chunk("KB-A")], result("Here's an answer [S1].", sources=[{}]), 150)
    assert entry["correct"] is False


def test_adversarial_uses_the_same_not_found_check():
    case = {"id": "D1", "category": "adversarial", "question": "q", "expected_not_found": True}
    entry = score_case(case, [], result(NOT_FOUND, not_found=True), 60)
    assert entry["correct"] is True


# ---------- score_case: ambiguous is logged, never auto-scored ----------
def test_ambiguous_case_is_never_auto_scored():
    case = {"id": "A1", "category": "ambiguous", "question": "q"}
    entry = score_case(case, [], result("Could you clarify?"), 80)
    assert entry["scored"] is False
    assert entry["correct"] is None


# ---------- fabricated citations are flagged regardless of category ----------
def test_fabricated_citation_is_recorded_even_on_an_otherwise_correct_answer():
    case = {"id": "E4", "category": "easy", "question": "q",
            "expected_doc_ids": ["KB-RETURNS"], "expected_contains": ["30 days"]}
    entry = score_case(case, [chunk("KB-RETURNS")],
                        result("30 days [S1][S9].", sources=[{}], invalid_citations=["S9"]), 110)
    assert entry["correct"] is True  # the fact itself was right
    assert entry["invalid_citations"] == ["S9"]
    assert any("fabricated" in r for r in entry["reasons"])


# ---------- summarize ----------
def test_summarize_computes_correctness_only_over_scored_cases():
    entries = [
        score_case({"id": "1", "category": "easy", "expected_doc_ids": ["A"], "expected_contains": ["x"]},
                   [chunk("A")], result("x", sources=[{}]), 100),
        score_case({"id": "2", "category": "easy", "expected_doc_ids": ["A"], "expected_contains": ["x"]},
                   [chunk("A")], result("wrong", sources=[{}]), 100),
        score_case({"id": "3", "category": "ambiguous"}, [], result("clarify?"), 100),
    ]
    summary = summarize(entries)
    assert summary["total_cases"] == 3
    assert summary["auto_scored_cases"] == 2  # ambiguous excluded
    assert summary["answer_correctness"] == 0.5


def test_summarize_citation_rate_only_counts_answered_cases():
    entries = [
        score_case({"id": "1", "category": "out_of_scope", "expected_not_found": True},
                   [], result(NOT_FOUND, not_found=True), 50),
        score_case({"id": "2", "category": "easy", "expected_doc_ids": ["A"], "expected_contains": ["x"]},
                   [chunk("A")], result("x", sources=[{}]), 100),
    ]
    summary = summarize(entries)
    assert summary["citation_rate"] == 1.0  # only the 1 answered case, and it had a source


def test_summarize_lists_failures_for_review():
    entries = [
        score_case({"id": "1", "category": "easy", "expected_doc_ids": ["A"], "expected_contains": ["x"]},
                   [chunk("A")], result("wrong"), 100),
    ]
    summary = summarize(entries)
    assert len(summary["failures"]) == 1
    assert summary["failures"][0]["id"] == "1"


def test_summarize_handles_zero_scored_cases_without_crashing():
    entries = [score_case({"id": "1", "category": "ambiguous"}, [], result("x"), 10)]
    summary = summarize(entries)
    assert summary["answer_correctness"] is None
