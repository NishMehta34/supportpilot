# SupportPilot — One-page engineering case study

**Project:** AI-assisted customer support prototype | **Duration:** 30-day engineering sprint | **Stack:** Python, FastAPI, Ollama, LangGraph, PostgreSQL/pgvector, MCP, Docker, pytest, vanilla JavaScript.

## Problem
Support teams need accurate, evidence-backed answers and safe automation. Free-form model responses alone cannot guarantee groundedness, authorization, or safe writes.

## Solution and scope
I built SupportPilot as a set of incremental engineering modules: retrieval over a knowledge base; typed read/write tools; a bounded agent workflow; JWT-protected multi-tenant API exercises; a browser console; evaluation, security, and resilience test suites. Ticket creation follows a draft → explicit human confirmation boundary enforced in code.

## Architecture and trade-offs
A local Ollama model keeps experimentation accessible. PostgreSQL/pgvector combines document search and tenant-aware database queries. LangGraph introduces explicit state transitions. FastAPI exposes typed endpoints, while a small HTML/JavaScript frontend avoids a separate build toolchain. Trade-off: the modules have not all been connected into one production-grade runtime; some development repositories remain in memory.

## Evidence
- Automated pytest suites for tools, API auth, UI, security, and failure helpers; run `python3 -m pytest -q` and record the actual result for your checkout.
- Day 24: 30-case synthetic fixture benchmark, **not** live agent performance.
- Day 27: adversarial tests and a documented threat model.
- Day 28: simulated failure drills and a readiness matrix identifying open production blockers.
- Human ticket confirmation demonstrated via Day 26 browser/API path.

## Engineering decisions
The model is not trusted with confirmation privileges. Tenant IDs must be derived from authenticated identity. Missing retrieval evidence should not be converted into invented citations. Resilience tests must distinguish simulated success from deployed-system readiness.

## Limitations and next iteration
The browser chat path is still a placeholder; agent citations and streaming are not integrated. Conversation persistence, durable idempotency, legacy tool tenant checks, and RAG/MCP tenant enforcement require completion. Next: wire the agent into the authenticated API, add PostgreSQL persistence, close security gaps, then run a measured live 50-case evaluation.

**Portfolio takeaway:** Demonstrates end-to-end engineering thinking and transparent risk reporting, rather than claiming a finished production service.
