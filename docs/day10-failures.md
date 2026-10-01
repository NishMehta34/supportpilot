# Day 10: Baseline scorecard and top failures

*Fill this in using your own run of `python3 scripts/run_eval.py`. The numbers
below are placeholders until you run it on your Mac.*

## Baseline scorecard

| Metric | Result |
|---|---|
| Answer correctness (24 auto-scored cases) | __ |
| Retrieval hit@5 | __ |
| Citation rate | __ |
| Fabricated citations | __ (should be 0) |
| Latency: avg / median / p95 (ms) | __ / __ / __ |

Full detail for every case: `artifacts/day10_scorecard.json`.

## How to find your top 5 failures

Open the scorecard and look at `summary.failures`, or just read the terminal
output for every line marked `[FAIL]`. For each one, the `reasons` field tells
you what went wrong:

- `"missing expected fact(s): [...]"` -> the answer didn't mention a fact it should have.
- `"expected document was not in the retrieved top-k"` -> a retrieval miss (Day 7/8 territory).
- `"expected not_found=True, got False"` -> the system answered when it should have declined.
- `"returned not-found, but evidence should have been available"` -> the similarity
  threshold in `app/rag.py` may be too strict, or retrieval under-performed.
- `"fabricated citation(s): [...]"` -> the model cited a source it was never given.

## Top 5 failures (fill in from your real run)

For each failure, name the likely cause and a concrete fix. Common causes seen
so far in this project, for reference:

| Cause pattern | Where it showed up before | Typical fix |
|---|---|---|
| Uneven/missing data in the embedded or indexed set | Day 7 (chunk sampling bug) | Check coverage before blaming the model |
| Similarity threshold too high or too low | New today | Try a few threshold values and re-run the eval |
| Chunk boundaries split a fact in half | Anticipated in Day 6 design | Adjust chunk size or add more overlap |
| Model answers from world knowledge instead of context | RAG-specific risk | Tighten the system prompt's "answer only from context" rule |
| Ambiguous wording between the question and the document | Possible in any case | Note it; some wording gaps are expected and acceptable |

### Failure 1
- **Case ID:**
- **What happened:**
- **Likely cause:**
- **Proposed fix:**

### Failure 2
- **Case ID:**
- **What happened:**
- **Likely cause:**
- **Proposed fix:**

### Failure 3
- **Case ID:**
- **What happened:**
- **Likely cause:**
- **Proposed fix:**

### Failure 4
- **Case ID:**
- **What happened:**
- **Likely cause:**
- **Proposed fix:**

### Failure 5
- **Case ID:**
- **What happened:**
- **Likely cause:**
- **Proposed fix:**

## The 6 ambiguous cases (not auto-scored)

Read each answer in the scorecard for cases A01-A06. For each, judge by hand:
did the system ask for clarification, decline gracefully, or confidently guess
at one interpretation? A confident guess on a genuinely ambiguous question is
a worse outcome than asking for clarification, even though no automated test
here catches that distinction.

| Case | What it did | Was that reasonable? |
|---|---|---|
| A01 | | |
| A02 | | |
| A03 | | |
| A04 | | |
| A05 | | |
| A06 | | |

## What I'd change for Day 20+ (guardrails) based on this run

(A few sentences: did the similarity threshold need tuning? Did any adversarial
case nearly succeed? Anything here worth remembering when you build guardrails
on Day 20.)
