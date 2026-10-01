"""Scoring functions for the Day 10 benchmark. Pure logic, no model or database."""

AUTO_SCORED_CATEGORIES = {"easy", "multi_document", "out_of_scope", "adversarial"}


def load_cases(path):
    import json
    cases = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def hit_at_k(expected_doc_ids, retrieved_chunks):
    """True if at least one expected document appears among the retrieved chunks.
    Returns None when the case has no expected documents (not applicable)."""
    if not expected_doc_ids:
        return None
    retrieved_ids = {chunk["doc_id"] for chunk in retrieved_chunks}
    return any(doc_id in retrieved_ids for doc_id in expected_doc_ids)


def contains_match(answer, expected_contains):
    """For each expected substring, whether it appears in the answer (case-insensitive).
    Returns (all_present, any_present, matched, missing)."""
    answer_lower = (answer or "").lower()
    matched = [s for s in expected_contains if s.lower() in answer_lower]
    missing = [s for s in expected_contains if s.lower() not in answer_lower]
    return len(missing) == 0, len(matched) > 0, matched, missing


def score_case(case, retrieved_chunks, result, elapsed_ms):
    """Score one case against the actual pipeline output. Never raises: an
    unexpected shape just gets recorded as a failure, not a crashed eval run.
    """
    category = case["category"]
    hit = hit_at_k(case.get("expected_doc_ids"), retrieved_chunks)

    entry = {
        "id": case["id"], "category": category, "question": case.get("question", ""),
        "hit_at_k": hit,
        "not_found": result["not_found"],
        "num_sources": len(result["sources"]),
        "invalid_citations": result["invalid_citations"],
        "elapsed_ms": elapsed_ms,
        "answer": result["answer"],
        "scored": category in AUTO_SCORED_CATEGORIES,
        "correct": None,
        "reasons": [],
    }

    if category in ("out_of_scope", "adversarial"):
        entry["correct"] = result["not_found"] == case["expected_not_found"]
        if not entry["correct"]:
            entry["reasons"].append(
                f"expected not_found={case['expected_not_found']}, got {result['not_found']}"
            )

    elif category in ("easy", "multi_document"):
        if result["not_found"]:
            entry["correct"] = False
            entry["reasons"].append("returned not-found, but evidence should have been available")
        else:
            all_present, any_present, matched, missing = contains_match(
                result["answer"], case.get("expected_contains", [])
            )
            entry["correct"] = all_present
            entry["any_fact_present"] = any_present
            entry["matched_facts"] = matched
            entry["missing_facts"] = missing
            if not all_present:
                entry["reasons"].append(f"missing expected fact(s): {missing}")
        if hit is False:
            entry["reasons"].append("expected document was not in the retrieved top-k")

    else:  # ambiguous: logged, not auto-scored
        entry["reasons"].append("ambiguous category: review the answer by hand")

    if entry["invalid_citations"]:
        entry["reasons"].append(f"fabricated citation(s): {entry['invalid_citations']}")

    return entry


def summarize(entries):
    """Turn a list of scored entries into the headline numbers for the scorecard."""
    scored = [e for e in entries if e["scored"]]
    with_hit = [e for e in entries if e["hit_at_k"] is not None]
    answered = [e for e in entries if not e["not_found"]]
    latencies = sorted(e["elapsed_ms"] for e in entries)

    def percentile(data, p):
        if not data:
            return 0
        index = min(len(data) - 1, int(len(data) * p))
        return data[index]

    return {
        "total_cases": len(entries),
        "auto_scored_cases": len(scored),
        "answer_correctness": round(sum(e["correct"] for e in scored) / len(scored), 3) if scored else None,
        "hit_at_k": round(sum(e["hit_at_k"] for e in with_hit) / len(with_hit), 3) if with_hit else None,
        "citation_rate": round(sum(e["num_sources"] > 0 for e in answered) / len(answered), 3) if answered else None,
        "fabricated_citations": sum(bool(e["invalid_citations"]) for e in entries),
        "latency_ms": {
            "avg": round(sum(latencies) / len(latencies), 1) if latencies else 0,
            "median": percentile(latencies, 0.5),
            "p95": percentile(latencies, 0.95),
            "max": max(latencies) if latencies else 0,
        },
        "failures": [e for e in scored if e["correct"] is False],
    }
