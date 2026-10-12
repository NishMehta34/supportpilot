# Day 16 — LangGraph conversation checkpointing

## Goal
A thread survives application restart with the order ID required to interpret a dependent follow-up. Use the same `thread_id` and trusted user/tenant namespace.

## Design
`START -> respond -> END`, where `respond` resolves narrow order references from persisted state and delegates the actual task to the Day 15 agentic RAG graph. LangGraph `SqliteSaver` stores checkpoints in `artifacts/day16-checkpoints.sqlite` for the offline demo. `open_conversation_graph` owns the SQLite connection; closing and reopening it simulates a process restart.

## What is persisted
Recent user/assistant text (12 messages maximum in the current state), last order ID, resolved question, route, final answer, and failure metadata. Do **not** persist Day 13 confirmation tokens, tool traces, or draft objects. SQLite checkpoints retain historical snapshots, so bounding the current `history` list does not delete older checkpoint rows.

## Limitations and security
- This is local development persistence, **not** production PostgreSQL checkpointing. Day 21+ can migrate to Postgres.
- `thread_config` partitions by tenant and user namespace but does **not** authenticate callers. The API must derive those IDs from a trusted login/session (Day 22), never from user-supplied arbitrary IDs.
- Only explicit order references (`ORD-1234`) and a few pronouns are resolved. This is not general semantic memory.
- Checkpoint files contain customer conversation text: keep them out of Git, restrict filesystem permissions, and implement retention/deletion before production.
- In-memory pending actions and tickets from Day 13 do **not** survive restart. That is not solved by graph checkpoints; persistence for side effects is a later production task.
- The Day 15 delegated agent may still have its known limitations (soft timeouts and demo tenant checks).

## Tests
`python3 -m pytest -q tests/test_conversation_memory.py`

## Demo
`python3 -m scripts.day16_demo`

Expected final line: `DAY 16 PASSED: context survived restart; threads isolated; 0 tickets created`
