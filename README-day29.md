# SupportPilot — AI Customer Support Engineering Capstone

> Portfolio-ready project overview. This is a prototype with documented integration and production-readiness gaps, **not a production deployment**.

## Problem
Support agents need reliable answers grounded in policy documents, safe access to order/customer tools, and explicit approval before consequential writes. SupportPilot explores these workflows using a local LLM, retrieval, typed tools, an agent graph, and a web console.

## What I built
- **Model and orchestration:** Ollama experiments, bounded tool execution, LangGraph workflow, checkpoints and selective memory prototypes.
- **Knowledge retrieval:** chunking, local embeddings, PostgreSQL/pgvector ingestion and tenant-filtered search, citation-oriented RAG experiments.
- **Business tools:** search knowledge, read orders/customers, draft support tickets. Ticket confirmation is a separate human-only action.
- **API and UI:** FastAPI endpoints, JWT/role/tenant checks, and a browser console for login, threads and human ticket confirmation.
- **Engineering:** MCP server, structured observability, guardrails, evaluation fixtures, Docker Compose, adversarial tests and failure drills.

**Integration status:** These components were built incrementally. The Day 26 browser chat still uses a placeholder; it does not yet invoke the real LangGraph/Ollama agent. In-memory thread storage loses state on restart. Tenant isolation in some legacy tools and RAG/MCP paths requires further work. Do not describe this as a fully integrated production system.

## Architecture
See [architecture diagram](docs/day29-architecture.md) and [design decisions](docs/day29-case-study.md).

## Run locally on macOS
Prerequisites: Python 3.13-compatible environment, Docker Desktop for database/Compose experiments, Ollama for model-backed exercises.

```bash
cd ~/Desktop/supportpilot
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pytest -q
```

### Browser demo (local, non-production authentication)
```bash
export SUPPORTPILOT_DAY26_LOCAL_DEMO=1
export SUPPORTPILOT_JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export SUPPORTPILOT_DAY26_DEMO_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(20))')"
printf 'username: demo-agent\npassword: %s\n' "$SUPPORTPILOT_DAY26_DEMO_PASSWORD"
uvicorn app.day26_api:app --host 127.0.0.1 --port 8001
```
Open http://127.0.0.1:8001. In the UI, create a thread, send a message (placeholder response), draft a ticket, and confirm it as a human.

### Docker stack (optional; separate deployment path)
```bash
docker compose -f docker-compose.day23.yml config --services
docker compose -f docker-compose.day23.yml up -d --build
docker compose -f docker-compose.day23.yml ps
```
Docker Compose starts infrastructure, but does not automatically make Day 26 browser chat a live model-backed agent.

## API and workflows
Inspect the OpenAPI docs at `/docs` for the API you started. Day 22 provides JWT login and tenant-scoped thread/chat/document endpoints; Day 26 adds UI delivery and protected ticket confirmation. Actual paths and roles should be verified against your checked-out version.

**Agent flow (target integration):** authenticated user → conversation → retrieval and permitted read tools → grounded response with citations → optional ticket draft → explicit human confirmation. The complete browser-to-agent path is **not wired**.

## Tests and evaluations
```bash
python3 -m pytest -q
python3 -m pytest -q tests/test_day27_security.py
python3 -m pytest -q tests/test_day28_resilience.py
python3 -m scripts.day28_demo
```
Day 24's 30-case fixture-mode results are **synthetic test evidence**, not measured live agent quality. Report measured live scores only after running a real adapter and recording its inputs, model version, and environment.

## Security and limitations
- No model-accessible ticket confirmation; human authorization is required.
- Day 27 strict tenant-checking adapter is not automatically wired into all retrieval/MCP paths.
- Legacy order/customer tools require additional ownership enforcement.
- Day 21/26 in-memory conversations are not durable.
- Day 28 idempotency is process-local, not durable across restart.
- Real agent-backed streaming, citations and tool traces are not connected to the browser.
- Local demo login is for development only.

## Demo and portfolio artifacts
- [3–5 minute demo script](docs/day29-demo-script.md)
- [One-page engineering case study](docs/day29-case-study.md)
- [Architecture](docs/day29-architecture.md)
- [Screenshot capture checklist](docs/day29-screenshots.md)
- [Portfolio verification tool](scripts/day29_portfolio_check.py)

## Next steps
1. Integrate authenticated browser chat with the real agent, citations, and tool traces.
2. Implement durable PostgreSQL thread state and transactional ticket idempotency.
3. Close tenant-isolation gaps across tools, RAG and MCP; rerun live adversarial tests.
4. Measure a 50-case live benchmark and compare against the Day 10 baseline on Day 30.
