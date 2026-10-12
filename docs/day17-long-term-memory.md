# Day 17 — Selective long-term memory

## Goal
Save only explicitly approved, durable user facts; retrieve relevant facts and allow deletion.

## Design
- SQLite table with `(tenant_id, user_id, key)` primary key. This is distinct from Day 16's conversation checkpoint database.
- Only `support_tier` and `preferred_language` are supported, with strict value allowlists.
- Writes require `consent=True` from a trusted application handler; do not let an LLM set this flag.
- `recall` retrieves no data for unrelated queries. `invoke_with_memory` adds allowlisted relevant values to the Day 16 graph input, scoped by the corrected Day 16 `thread_config`.
- `forget` removes one fact or all facts for a tenant/user from the active memory table. Reopen the database to confirm deletion.

## Threats and limits
- Caller identity must come from authenticated application context. This local demo does not implement authentication.
- A memory fact is **not proof of account entitlement**: support tier must be verified against an authoritative customer system before granting privileges.
- SQLite is local-development storage, not a multi-tenant production authorization layer.
- SQL DELETE does not guarantee forensic erasure from SQLite WAL, free pages, filesystem snapshots, backups, or Day 16 checkpoint history. A production erasure workflow must address all copies and retention rules.
- The bridge injects relevant facts into the question text, so those facts can enter Day 16 checkpoint history. For strict deletion across all persisted stores, redesign the graph to pass ephemeral memory context rather than persisting the enriched question.
- `recall` uses a deliberately small keyword relevance filter. It is not semantic retrieval, and will miss some phrasings.
- The model may ignore a language preference; this demo verifies context delivery, not model compliance.
- The memory store contains no confirmation tokens, ticket drafts, or arbitrary free-form notes.

## Run
`python3 -m pytest -q tests/test_long_term_memory.py`
`python3 -m scripts.day17_demo`

## Self-check
1. Why is Day 16 checkpoint state different from Day 17 user memory?
2. Why must consent be checked by the application, not the model?
3. Does deleting a row guarantee erasure from checkpoints/backups? (No.)
4. Why is a remembered support tier not an authorization source?
