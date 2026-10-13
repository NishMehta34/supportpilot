# Day 28 — Production-readiness and resilience evidence

## Scope and honesty
These are deterministic, offline **failure simulations** against opt-in resilience helpers, not end-to-end tests of the deployed SupportPilot stack. The helpers are not automatically wired into the Day 26 UI, Day 22 API, Day 15 agent, or Day 18 MCP server.

## Failure-mode matrix

| Critical failure mode | Expected recovery | Evidence | Status |
|---|---|---|---|
| Model unavailable | Return safe unavailable status, no exception details | `test_model_unavailable_graceful` | PASS (simulated) |
| Database unavailable | Readiness false, no secret exposure | `test_database_unavailable_graceful`, `test_readiness_reports_partial_outage` | PASS (simulated) |
| Slow retrieval | Time out, distinguish failure from zero hits | `test_slow_retrieval_timeout` | PASS (simulated; worker may continue) |
| Concurrent chats | Isolate tenant/thread state and avoid races | `test_concurrent_requests_deduplicated` only tests a write helper | OPEN (live chat untested) |
| Restart with active threads | Recover thread history from durable store | `test_restart_active_thread_loss_detected` detects lost state | FAIL / OPEN (no persistence) |
| Duplicate ticket requests | One durable draft per tenant/user/idempotency key, including across restarts | `test_duplicate_ticket_request_deduplicated`, `test_concurrent_requests_deduplicated` | PASS in-process; OPEN across restart |
| Empty retrieval | Return no evidence, never invent citations | `test_empty_retrieval_is_distinct` | PASS (simulated) |

## Risk notes
1. `guarded_call` uses worker threads. A timeout does **not** stop a running thread. Use only for read-only calls; do not wrap ticket creation/confirmation in it. Prefer native HTTP/database timeouts in production.
2. `ScopedIdempotency` is process-local, serializes actions behind a single lock, and loses its state on restart. For production, use a database unique constraint on `(tenant_id, user_id, idempotency_key)` and a transaction with a persisted result; make confirmation transactional.
3. Day 21 repositories are in memory. A restart loses thread state. Implement a durable repository and test real restart/reconnect before claiming readiness.
4. The Day 26 chat path is a placeholder. Real concurrent agent chat and recovery are not validated here.
5. Day 27 high-priority findings (tenant isolation in legacy tools and RAG/MCP) remain deployment blockers.

## Live acceptance drill on macOS (manual; do not run against production data)
1. Start `docker compose -f docker-compose.day23.yml up -d --build`, check `docker compose -f docker-compose.day23.yml ps` and `python3 -m scripts.day23_check`.
2. Run `python3 -m pytest -q tests/test_day28_resilience.py` and `python3 -m scripts.day28_demo`.
3. **Model outage:** `docker compose -f docker-compose.day23.yml stop ollama`; exercise actual model-backed chat (once integrated); capture HTTP response and recovery time. Restart with `start ollama`.
4. **DB outage:** `docker compose -f docker-compose.day23.yml stop db`; exercise DB-backed endpoint (once integrated); capture HTTP response and recovery time. Restart with `start db`.
5. **Slow retrieval:** inject a controlled 2-second delay into a real retrieval adapter; check timeout, fallback, and request latency.
6. **Concurrent chats:** send 20 parallel requests across two users and threads; check isolation, failures, and latency.
7. **Restart:** create a thread and message; restart API container; verify thread and history remain available. The current in-memory repository is expected to FAIL.
8. **Duplicate ticket:** send the same idempotency key concurrently and across API restarts; verify one persisted draft/ticket. Current in-memory helper is expected to FAIL across restart.
9. Record actual evidence, timings, environment, and pass/fail in a new `artifacts/day28-live-readiness.json` (do not label offline evidence as live).

## Definition of done
Every critical mode has documented expected behavior and a test. **The workbook's production-readiness goal remains incomplete until open live/durable scenarios are fixed and verified.**
