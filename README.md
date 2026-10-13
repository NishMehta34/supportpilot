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

## Day 20 — Guardrails and execution budgets

`app/guardrails.py` adds a per-request tool boundary with input limits, call budgets, read timeouts, restricted read retries, and no automatic write retries. It delegates authorization and ticket staging to Day 13 `SupportToolbox`.

```bash
python3 -m pytest -q tests/test_guardrails.py
python3 -m scripts.day20_demo
cat artifacts/day20-budget.json
```

See `docs/day20-guardrails.md` for threat model and limitations. In particular, Python thread timeouts are not hard cancellation, and this wrapper is not yet wired into all LangGraph paths.

## Day 21 — Modular FastAPI service

Run `uvicorn app.day21_api:app --reload`, then open http://127.0.0.1:8000/docs. Endpoints: `/health`, `/chat`, `/threads`, `/documents`, `/tickets`. The new API uses Pydantic contracts, FastAPI dependency injection, application services and a local repository. Tests: `python3 -m pytest -q tests/test_day21_api.py`. Demo: `python3 -m scripts.day21_demo`. **Development scaffold only:** no JWT authentication, no live agent wiring, no document embeddings, and no persistent API repositories yet. Ticket creation remains draft-only. See `docs/day21-service.md`.

## Day 22 — Local JWT auth and tenant-aware API

- Run `uvicorn app.day22_api:app --reload` (replaces the unauthenticated Day 21 API for this exercise).
- Set `SUPPORTPILOT_JWT_SECRET` to a strong random secret of at least 32 characters. Never commit the secret.
- The default app has no users. For tests and the demo, explicit local-only accounts are injected through `create_app(users=...)`.
- `/login` returns a signed 30-minute bearer token; `/me`, `/threads`, `/chat`, `/documents`, and `/tickets` require it.
- Tenant and user scope is taken from the verified token, never request-supplied fields. Viewer role cannot create documents or ticket drafts. Ticket confirmation is not exposed.
- Run `python3 -m pytest -q tests/test_day22_auth.py` and `python3 -m scripts.day22_demo`.
- See `docs/day22-auth.md` for limitations and remaining RAG/MCP authorization work.

## Day 23 — Docker Compose stack

Day 23 adds `Dockerfile`, `docker-compose.day23.yml`, `.dockerignore`, `.env.day23.example`, a smoke-check script, and deployment tests. On macOS install Docker Desktop, then follow `docs/day23-docker.md` to create `.env`, build, and start the API + Postgres/pgvector + Ollama services. Visit http://localhost:8000/docs. The API is the Day 22 scaffold, not yet a fully wired Ollama/pgvector application. Never commit `.env` or use the default empty login account registry in production.

## Day 24 — Agent regression benchmark

Run `python3 -m pytest -q tests/test_day24_evals.py` and `python3 -m evals.run`. The default run is **synthetic fixture validation**, not a model quality benchmark. JSON output: `artifacts/day24_report.json`. The live mode `python3 -m evals.run --mode live` requires Ollama/pgvector and currently fails the gate until the six tool cases are integrated. See `docs/day24-evaluation.md`.

## Day 25 — AI-assisted engineering review

Focused PR exercise: reject invalid (negative, NaN, or infinite) latency measurements in the Day 24 evaluation runner, preventing misleading benchmark reports. The implementation is in `evals/run.py`; regression tests are in `tests/test_day25_eval_hardening.py`. Follow `docs/day25-ai-coding-review.md` for the AI coding prompt, human review checklist, tests, and PR description. The benchmark fixture is synthetic; real agent evaluation remains a separate task.

## Day 26 — Browser support console

Run `uvicorn app.day26_api:app --reload --host 127.0.0.1` and open http://127.0.0.1:8000/. A framework-light UI provides JWT login, thread list, chat status, citations/tool activity placeholders, and human-only ticket draft confirmation. Use opt-in local demo credentials described in `docs/day26-ui.md`. Tests: `python3 -m pytest -q tests/test_day26_ui.py`. Demo: `python3 -m scripts.day26_demo`.

**Scope:** Chat remains an injectable Day 21 stub by default; real LLM integration, streaming, durable database storage and production identity provisioning are not complete.

## Day 27 — Adversarial testing and security review

- `tests/test_day27_security.py`: 17 offline abuse-case tests spanning JWTs, tenant isolation, tools, ticket confirmation, input limits, repeat requests, retrieval and errors.
- `app/day27_security.py`: strict tenant-checked retrieval adapter for **new integrations**; not yet wired into all live agent/MCP paths.
- `app/support_tools.py`: targeted patch preventing raw exception messages from leaking in generic tool failures.
- `scripts/day27_demo.py`: writes `artifacts/day27_security.json`.
- `docs/day27-threat-model.md`: trust boundaries, mitigations, **unresolved high-priority findings** and integration plan.

Run `python3 -m pytest -q tests/test_day27_security.py tests/test_support_tools.py` and `python3 -m scripts.day27_demo`. This is an adversarial test package, **not** a claim of production security approval.

## Day 28 — Resilience and production-readiness drills

- Run `python3 -m pytest -q tests/test_day28_resilience.py`.
- Run `python3 -m scripts.day28_demo` for offline simulated failure evidence in `artifacts/day28_readiness.json`.
- Review `docs/day28-readiness.md` for the seven-scenario readiness matrix and live Mac/Docker drill plan.
- **Limitations:** No automatic wiring to live APIs, no durable idempotency, no persisted thread recovery, and no live concurrency benchmark. Do not call the service production-ready on the basis of the offline tests.
