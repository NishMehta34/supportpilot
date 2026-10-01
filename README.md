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
