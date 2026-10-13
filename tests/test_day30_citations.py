"""Day 30: Citation grounding regression tests."""

from app.support_agent import enforce_retrieval_grounding


def test_rejects_unretrieved_citation():
    """A document not retrieved must not be cited."""
    result = {
        "final_answer": "Premium costs $99 [KB-PRICING].",
        "trace": [],
    }

    checked = enforce_retrieval_grounding(result)

    assert checked["grounding_status"] == "unsupported_citation"
    assert "KB-PRICING" in checked["unsupported_citations"]
    assert "KB-PRICING" not in checked["final_answer"]


def test_answer_without_citations_is_not_automatically_verified():
    """No citation and no trace does not prove an answer is grounded."""
    result = {
        "final_answer": "Premium costs $99.",
        "trace": [],
    }

    checked = enforce_retrieval_grounding(result)

    assert checked["grounding_status"] == "not_applicable"


def test_rejects_citation_when_wrong_document_was_retrieved():
    """Retrieving one document does not authorize citing another."""
    result = {
        "final_answer": "Premium costs $99 [KB-PRICING].",
        "trace": [
            {
                "tool": "search_kb",
                "result": {
                    "results": [
                        {
                            "doc_id": "KB-ACCOUNT",
                            "section": "Membership tiers",
                            "snippet": "Premium membership costs $99.",
                        }
                    ]
                },
            }
        ],
    }

    checked = enforce_retrieval_grounding(result)

    assert checked["grounding_status"] == "unsupported_citation"
    assert checked["retrieved_kb_doc_ids"] == ["KB-ACCOUNT"]


def test_accepts_citation_for_retrieved_document():
    """A matching citation passes the document-ID check."""
    result = {
        "final_answer": "Standard members have 30 days [KB-RETURNS].",
        "trace": [
            {
                "tool": "search_kb",
                "result": {
                    "results": [
                        {
                            "doc_id": "KB-RETURNS",
                            "section": "Return window",
                            "snippet": "Standard members have 30 days.",
                        }
                    ]
                },
            }
        ],
    }

    checked = enforce_retrieval_grounding(result)

    assert checked["grounding_status"] == "evidence_retrieved"
    assert checked["final_answer"] == result["final_answer"]

def test_section_qualified_citation_is_rejected():
    """A section name must not appear inside citation brackets."""
    result = {
        "final_answer": (
            "The replacement ships within 2 business days "
            "[KB-WARRANTY > Replacement process]."
        ),
        "trace": [
            {
                "tool": "search_kb",
                "result": {
                    "results": [
                        {
                            "doc_id": "KB-WARRANTY",
                            "section": "Replacement process",
                            "snippet": "Replacements ship within 2 business days.",
                        }
                    ]
                },
            }
        ],
    }

    original_answer = result["final_answer"]

    checked = enforce_retrieval_grounding(result)

    assert checked["grounding_status"] == "invalid_citation_format"
    assert checked["final_answer"] != original_answer
    assert "couldn't verify" in checked["final_answer"]