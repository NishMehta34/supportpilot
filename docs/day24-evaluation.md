# Day 24 — Agent regression evaluation

## Workbook requirements

`python -m evals.run`, 30 cases, JSON output, routing accuracy, retrieval hit@5, citation rate, tool success, latency, regression gate.

## Important: fixture vs live

Default `--mode fixture` is a deterministic **synthetic** adapter: it validates evaluator math, test wiring and gate behavior. A 100% fixture score is **not** evidence that SupportPilot's LLM, retrieval or tools perform at 100%.

`--mode live` calls the existing Day 10 RAG pipeline for 24 RAG cases, but deliberately marks 6 tool cases unsupported and **fails** the gate. Full live acceptance requires implementing an authenticated Day 15/18 tool adapter and rerunning all 30 cases. Do not replace the committed fixture baseline with live results; establish a separate real baseline after completing live tool coverage.

The six original ambiguous Day 10 questions were replaced with six tool cases for this Day 24 suite. Twenty-four RAG questions remain from the original workbook dataset. The live adapter currently reports route=rag for RAG cases, so routing accuracy is not a genuine classifier evaluation until wired to actual agent routing.

## Run

```bash
python3 -m pytest -q tests/test_day24_evals.py
python3 -m evals.run
python3 -m evals.run --mode live --report artifacts/day24-live.json
```

The live command requires Ollama and the ingested Nimbus database, and is expected to fail its quality gate while tool evaluation is unsupported. `--report` selects a path for the JSON report. The evaluator does not write user messages or model outputs into its report; case IDs and aggregate metadata only.

## Quality gate

Absolute thresholds: routing >=90%, retrieval hit@5 >=85%, citation rate >=85%, tool success >=90%. A decrease of more than 5 percentage points relative to baseline fails. p95 latency more than 1.5x a nonzero baseline fails. Unsupported cases fail. Errors are recorded by exception type without raw exception messages.

## Next integration step

Wire the live adapter to the authenticated, tenant-scoped Day 15 agent and Day 18 MCP dispatcher, record real tool outcomes and citations, then capture and review a real baseline. Keep human ticket confirmation outside the agent.
