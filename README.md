# SupportPilot

**Goal:** Build a production-style AI customer-support agent using local, open-source tools.

## My machine
- MacBook / Mac with Apple M4
- RAM: 24 GB
- macOS: Version 15.6.1


## How to run Day 1
1. Install Ollama and run `ollama run qwen3` once to download the model.
2. Make sure Ollama is running.
3. Run `python3 app/llm_demo.py`
4. The result is saved to `artifacts/day01.json`

## How to run Day 2
1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `pytest` (no model needed)
4. `python3 -m app.classify_demo` (Ollama must be running)
5. Results are saved to `artifacts/day02.json`

## How to run Day 3
1. Activate the environment: `source .venv/bin/activate`
2. `pytest` (no model needed)
3. `python3 -m app.tool_demo` (Ollama must be running)
4. Transcripts are saved to `artifacts/day03.json`

## How to run Day 4
1. Activate the environment: `source .venv/bin/activate`
2. `pytest` (no model needed)
3. `python3 -m app.agent_demo` (Ollama must be running)
4. Summary: `artifacts/day04.json`; per-run traces: `artifacts/traces/`

The agent is bounded: max 6 steps, stops on repeated identical tool calls.

## How to run Day 5
1. `source .venv/bin/activate`
2. `bash scripts/test.sh` runs all tests (no model needed)
3. Bug log: `docs/day05-bugs.md`

Tests use `FakeAdapter` (app/model_adapter.py), a scripted stand-in for the real model.

## Day 6: RAG design
- Design document: `docs/rag-design.md` (includes the architecture diagram)
- Knowledge base (5 documents): `data/kb/`
- Preview the chunking: `python3 scripts/preview_chunks.py`

## How to run Day 7
1. `ollama pull embeddinggemma` (one-time)
2. `source .venv/bin/activate`
3. `pytest` (no model needed)
4. `python3 scripts/embed_kb.py` (embeds 20 chunks; Ollama must be running)
5. `python3 scripts/similarity_demo.py` (tests 5+ queries against those chunks)
6. Results: `artifacts/day07_embeddings.json`, `artifacts/day07_notes.json`, `artifacts/day07_notes.md`

## How to run Day 8
1. `docker compose up -d` starts Postgres + pgvector
2. `pip install -r requirements.txt`
3. `pytest` (uses a fake database, no Docker needed)
4. `python3 scripts/ingest.py` loads the Nimbus knowledge base (tenant: nimbus)
5. `python3 scripts/ingest.py --tenant acme --kb-dir data/kb_other_tenant` loads a second tenant
6. `python3 scripts/search_db.py "your question"` searches (add `--tenant acme` to scope it)

Schema: `db/init.sql`. Every chunk carries a `tenant_id`; every search filters by it.

## How to run Day 9
1. `docker compose up -d` (database) and Ollama running
2. `pip install -r requirements.txt`
3. `pytest` (95 tests, no model or database needed)
4. `uvicorn app.main:app --reload` starts the API on http://localhost:8000
5. Try it: `http://localhost:8000/docs`, or `python3 scripts/ask_demo.py` for the 20-question benchmark
6. Results: `artifacts/day09.json`

Every answer is grounded in retrieved evidence and cites its sources as [S1], [S2].
If confidence is too low, the API says so instead of guessing.

## How to run Day 10
1. `docker compose up -d` and Ollama running
2. `pytest` (115 tests, no model needed)
3. `python3 scripts/run_eval.py` runs the 30-case benchmark
4. Results: `artifacts/day10_scorecard.json`, writeup: `docs/day10-failures.md`

Baseline (fill in from your run): correctness __, hit@5 __, citation rate __.

## How to run Day 11
1. `source .venv/bin/activate`
2. `pytest` (121 tests, no model needed)
3. `python3 scripts/alfred_demo.py` (Ollama must be running)
4. Notes: `docs/day11-notes.md`, state diagram: `docs/day11-state-diagram.md`,
   framework comparison: `docs/day11-primitive-vs-framework.md`
5. Traces: `artifacts/day11_traces/`

Alfred reuses the exact same `run_agent` loop from Day 4, with a different toolbox.

## How to run Day 12
1. `source .venv/bin/activate`
2. `pytest` (126 tests)
3. `python3 scripts/raw_version.py`
4. `pip install "smolagents[litellm]"` then `python3 scripts/smolagents_version.py`
5. `python3 scripts/mini_agent_version.py`
6. Comparison: `docs/day12-comparison.md`

Decision: SupportPilot keeps the raw loop for the rest of the sprint (see comparison doc for why).

## How to run Day 13
1. `source .venv/bin/activate`
2. `pytest` (167 tests, no model needed)
3. `python3 scripts/support_demo.py` (Ollama running; database optional)
4. Design and threat table: `docs/day13-write-safety.md`; results: `artifacts/day13.json`

Rule: the AI may inspect and draft; only a human may confirm. Enforced in code
(app/support_tools.py), not in the prompt.

## Day 14 — LangGraph workflow

The support workflow uses LangGraph with explicit state and routing:

START -> classify -> retrieve -> tool_decision
-> answer/escalate -> END

Run:
- `python3 -m pytest -q`
- `python3 -m scripts.day14_demo`

Design: `docs/day14-langgraph.md`
Evidence: `artifacts/day14.json`

The Day 13 human-confirmation boundary is preserved.

## Day 15 — Agentic RAG

SupportPilot combines LangGraph orchestration with
model-selected business tools.

Tools:
- search_kb
- get_order
- get_customer
- create_ticket (draft only)

Run:
- python3 -m pytest -q
- python3 -m scripts.day15_demo
- python3 -m evals.day15_run

Evidence:
- artifacts/day15.json
- artifacts/day15-benchmark.json
- docs/day15-agentic-rag.md

Safety: The AI cannot confirm or create a ticket
without the separate human confirmation process.
## Day 16 — Persistent conversation checkpoints

Install `langgraph-checkpoint-sqlite` and run:

```bash
python3 -m pytest -q tests/test_conversation_memory.py
python3 -m scripts.day16_demo
cat artifacts/day16.json
```

Design: `docs/day16-memory.md`. The local SQLite file is sensitive and should never be committed. This is thread-scoped short-term memory, not Day 17 long-term user memory.

## Day 17 — Selective long-term memory

- `app/long_term_memory.py`: consent-gated, tenant/user-scoped SQLite preference store.
- `python3 -m pytest -q tests/test_long_term_memory.py`: five safety/memory tests.
- `python3 -m scripts.day17_demo`: offline persistence, relevance, isolation, deletion demo.
- `artifacts/day17.json`: generated evidence; `docs/day17-long-term-memory.md`: design and limitations.
- Checkpoint data and memory databases must not be committed to Git.


## Day 18 — Model Context Protocol (MCP)

SupportPilot exposes `get_order`, `search_kb`, and draft-only `create_ticket` through an MCP stdio server. The MCP interface calls the same `SupportToolbox.execute()` business logic as the native agent.

```bash
python3 -m pytest -q tests/test_mcp_server.py
python3 -m scripts.day18_mcp_client
```

Evidence: `artifacts/day18.json`. Design, tool schemas, safety notes and limitations: `docs/day18-mcp.md`.

**Safety:** no MCP tool can confirm ticket creation. The demo's KB retriever is a stub; production auth and tenant authorization remain future work.

## Day 19 — Observability

Run `python3 -m pytest -q tests/test_observability.py tests/test_health_day19.py` and `python3 -m scripts.day19_demo`.

Structured diagnostics: `app/observability.py`. Design: `docs/day19-observability.md`. Ten-run report: `artifacts/day19-report.json`. Existing liveness endpoint: `GET /health`.

Logs are sanitized metadata, not raw conversations or confirmation tokens. The demo uses synthetic failures, not a live model.
