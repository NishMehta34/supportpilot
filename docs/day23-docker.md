# Day 23 — Dockerized SupportPilot development stack

## Architecture
`docker-compose.day23.yml` starts three services: FastAPI (Day 22 app), PostgreSQL 16 with pgvector, and Ollama. The API waits for database and Ollama healthchecks. Database and Ollama ports are not published to the host. API is bound to localhost:8000. Persistent named volumes hold database and model files.

## Mac setup
Install Docker Desktop and start it. From the project root:

```bash
cp .env.day23.example .env
python3 - <<'PY'
from pathlib import Path
import secrets
p=Path('.env')
s=p.read_text().replace('REPLACE_WITH_RANDOM_PASSWORD',secrets.token_urlsafe(32)).replace('REPLACE_WITH_RANDOM_48_BYTE_SECRET',secrets.token_urlsafe(48))
p.write_text(s)
PY
chmod 600 .env
docker compose -f docker-compose.day23.yml up -d --build
python3 -m scripts.day23_check
```

`docker compose -f docker-compose.day23.yml exec ollama ollama pull qwen3` downloads the model. On Apple Silicon the Ollama container may be CPU-only and slower than native macOS Ollama; Docker Desktop memory/disk must be adequate.

## Verification
`docker compose -f docker-compose.day23.yml ps` should show three healthy services. `curl -f http://127.0.0.1:8000/health` returns `{"status":"ok"}`. `http://localhost:8000/docs` exposes the Day 22 OpenAPI docs.

## Troubleshooting
- `docker compose -f docker-compose.day23.yml config`: validate YAML and environment substitutions.
- `docker compose -f docker-compose.day23.yml logs -f api`: inspect API startup.
- `docker compose -f docker-compose.day23.yml logs -f db`: inspect schema initialization.
- `docker compose -f docker-compose.day23.yml logs -f ollama`: inspect model service.
- `docker compose -f docker-compose.day23.yml down`: stop services but retain volumes.
- `docker compose -f docker-compose.day23.yml down -v`: DELETES persisted Postgres data and Ollama models.

## Known limitations
- Day 22 default API has no login users; authentication requires a trusted account bootstrap.
- Day 22 chat remains a scaffold; it does not automatically invoke Ollama.
- Day 22 repository remains in-memory; Postgres is available but is not yet wired into the API service.
- Ollama is healthy before any model is downloaded; pull `qwen3` separately.
- `app.model_adapter.OllamaAdapter` defaults to localhost and does not automatically read `OLLAMA_URL`; instantiate it with the container URL explicitly when wiring real chat.
- The Postgres init script only runs for a NEW volume; schema migrations are needed for existing databases.
- Images are version-range/latest based and not digest-pinned. Pin digests and add CI container smoke tests before production.
- A green healthcheck verifies liveness, not complete feature readiness or secure end-to-end tenant authorization.
