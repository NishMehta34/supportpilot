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
