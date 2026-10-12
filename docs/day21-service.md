# Day 21 — Production-style FastAPI boundaries (development scaffold)

## Workbook requirements

FastAPI path operations, request models, dependencies and application structure. Endpoints: `/chat`, `/threads`, `/documents`, `/tickets`, `/health`. Deliver clean project structure, OpenAPI and endpoint tests.

## Layers

- `day21_api.py`: HTTP routers, dependency injection, OpenAPI.
- `day21_models.py`: Pydantic request models and input bounds.
- `day21_services.py`: application operations; tool dispatch through Day 13 SupportToolbox.
- `day21_repositories.py`: in-memory local repositories; tenant/user-scoped lookup.
- Existing `conversation_memory.py`, `agentic_rag.py`, `support_tools.py`, `retrieval.py`, `db.py`, `model_adapter.py`: agent orchestration, tools, retrieval, persistence, model.

## Deliberate limits (read before production)

- **No authentication:** tenant/user values come from client input. A malicious client can impersonate another user. Day 22 must replace this with verified JWT claims; filtering alone is not authorization.
- `/chat` accepts an injected handler but returns `configured=false` by default. It is not wired to the Day 16 LangGraph or Ollama. Do not claim end-to-end agent functionality from the scaffold.
- `/documents` stores text in memory and lists metadata only; it does not chunk, embed or index documents. Data disappears at restart.
- `/tickets` POST stages a draft using the existing Day 13 toolbox. No HTTP confirmation endpoint is exposed, and `GET /tickets` shows only confirmed tickets (none until a separate trusted human confirmation workflow is wired).
- Pending actions and tickets are in memory. The default local demo uses a hardcoded agent role for draft creation, not verified authorization.
- `/health` is a liveness endpoint, not a readiness check.
- Use a single worker in this demo; in-memory repositories are not shared across processes.

## Local commands

```bash
python3 -m pytest -q tests/test_day21_api.py
python3 -m scripts.day21_demo
uvicorn app.day21_api:app --reload
```

Browse http://127.0.0.1:8000/docs to inspect OpenAPI and test endpoints.

## Next production tasks

Day 22: JWT authentication, verified identity, tenant authorization at API/tool/DB layers. Later: durable repositories, agent wiring, ingestion, readiness checks, human review UI, centralized guardrails.
