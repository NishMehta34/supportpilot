# Day 25 — AI-assisted issue and human review

## Source-of-truth workbook requirement
Choose one issue; use an AI coding tool to inspect, plan, implement, test, summarize; manually review every diff and run tests and evals; submit one real PR. The package is a **proposed patch**, not a submitted PR or evidence of human review.

## Issue: malformed timing data can contaminate evaluation reports

Day 24's `evaluate()` converted adapter-provided `latency_ms` to `float` without validating its domain. A negative latency is impossible, and NaN/Infinity can enter reports and lead to misleading percentile calculations or non-standard JSON. This is a correctness and reporting-integrity issue, not a model-accuracy fix.

## Plan
1. Validate each supported result's latency as finite and nonnegative before writing an evaluation entry.
2. Let the existing per-case exception handler turn malformed latency into a failed evaluation case, recording only `error_type` (not the raw value or exception text).
3. Test negative, NaN, positive and negative infinity, malformed text, and a valid positive measurement.
4. Run new tests, Day 24 tests, the fixture evaluation, and full suite.
5. Review the exact diff; make one focused PR with test output.

## Files changed
- `evals/run.py`: import `math`; check `math.isfinite(latency)` and `latency >= 0` before appending a scored result.
- `tests/test_day25_eval_hardening.py`: six tests, five invalid inputs plus one valid control.

## AI coding prompt (paste into Codex/Claude Code/Cursor)

> Inspect `evals/run.py` and `tests/test_day24_evals.py`. Identify a real correctness issue with malformed latency values in the Day 24 evaluator. Propose a minimal patch that rejects negative, NaN, and infinite latency without logging sensitive exception messages. Add deterministic regression tests. Do not change benchmark thresholds, expected routes, fixture outcomes, or any authentication/ticket code. Show a plan before editing; afterward show the diff, test commands, and limitations. Do not commit or push without my review.

## Human code review checklist
- [ ] Confirm only the intended evaluator and new test file changed.
- [ ] Confirm malformed latency results become scored failures rather than silently omitted.
- [ ] Confirm finite nonnegative latency remains valid.
- [ ] Confirm no raw prompts, secrets, or exception messages are logged.
- [ ] Run new and Day 24 tests.
- [ ] Run `python3 -m evals.run` and inspect JSON report.
- [ ] Run full pytest suite; record the real result.
- [ ] Explain the change in your own words and open a PR.

## Limitations
This patch does not improve actual agent accuracy, wire live MCP tools into Day 24 evals, or submit a PR. The fixture benchmark remains synthetic. Other malformed adapter outputs (e.g., incorrect `retrieved_doc_ids` types) are outside this focused issue.
