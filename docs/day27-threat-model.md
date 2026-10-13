# Day 27 — Adversarial security review and threat model

## Workbook scope
Prompt injection; unauthorized ticket creation; cross-tenant retrieval; malformed tool arguments; tool failure; oversized input; repeated requests; empty retrieval. Done criterion: **all high-priority abuse cases blocked or safely contained**.

## Trust boundaries
1. Browser / external caller -> JWT-verifying FastAPI dependency. Request-supplied tenant or user IDs must never grant authority.
2. User / retrieved content -> LLM. Retrieved text and tool outputs are **untrusted data**, never instructions or proof of authorization.
3. LLM -> `SupportToolbox.execute`. Model can read and stage drafts, but cannot call `confirm`.
4. Retriever -> tool response. Tenant isolation must be enforced by the database query **and** checked on returned chunks.
5. Human -> `POST /ticket-drafts/{draft_id}/confirm`. Role, tenant, owner, expiry and token are validated by trusted code.

## Threats, mitigations, evidence
| Threat | Defense / evidence | Status |
|---|---|---|
| Missing / invalid JWT | FastAPI bearer dependency; Day 27 API tests | Covered in local API |
| Cross-tenant thread/chat/document access | Owner/tenant repository scope; API tests | Covered in local API |
| Cross-tenant draft confirmation | Tenant check in PendingActionStore; API test | Covered in local API |
| Prompt injection requesting `confirm_ticket` | Tool allowlist; model cannot call confirm | Covered for tool interface |
| Malformed tool args | Validation; no confirmed ticket created | Covered |
| Oversized chat input | Pydantic 2000-character limit | Covered |
| Tool exceptions | Day 27 patch suppresses exception details in generic tool errors | Fixed |
| Empty / failed retrieval | Empty result or safe unavailable error | Covered |
| Repeated drafts and confirmations | Draft deduplication and one-time confirmation | Covered sequentially |
| Foreign or unscoped RAG chunks | New `tenant_checked_retrieval` adapter fails closed | Implemented, **not globally wired** |
| Legacy `get_order` / `get_customer` tenant ownership | Existing tool reads global mock records without tenant ownership check | **OPEN — HIGH** |
| Day 15 live RAG / Day 18 MCP identity propagation | Existing code has not been end-to-end secured | **OPEN — HIGH** |
| Concurrent duplicate confirmation | In-memory stores lack a DB transaction/unique constraint | **OPEN — HIGH for production** |
| Credential provisioning / rate limits / persistent storage | Local demo accounts and in-memory state | **OPEN for production** |

## Integration instructions for real RAG
```python
from app.day27_security import tenant_checked_retrieval
from app.support_tools import SupportToolbox, UserContext

toolbox = SupportToolbox(
    UserContext(user_id=verified_user, tenant_id=verified_tenant, role=verified_role),
    retrieve_fn=tenant_checked_retrieval(your_retrieve_fn),
)
```
`your_retrieve_fn(query, tenant_id, limit)` **must** return a list of dictionaries with `tenant_id`, `doc_id`, `section`, `content`, and `score`. The adapter rejects missing/mismatched tenant IDs, malformed scores, and invalid data. It cannot substitute for SQL row-level isolation. Do not attach this adapter to a retriever that cannot provide trustworthy tenant metadata; update the DB schema/query first.

## Why this is not a full security sign-off
Tests are deterministic and offline. They do not test an actual malicious LLM, real PostgreSQL row-level security, the deployed MCP transport, or concurrent multi-process traffic. The workbook's **Done When** requirement is therefore **not yet satisfied**: address all OPEN HIGH issues before a public deployment. Do not use the local demo authentication system in production.

## Recommended next fixes (priority order)
1. Add tenant ownership columns to order/customer storage and require tenant-aware lookups for every read tool. Deny access when ownership cannot be proven.
2. Wire strict retrieval validation into every Day 15/16 agent, Day 18 MCP, and authenticated API path; add integration tests against a seeded multi-tenant database.
3. Replace in-memory confirmation with transactional persistent storage, unique draft IDs and idempotency constraints; test concurrent confirmations.
4. Test live model prompt injections, JWT abuse, input limits, retries, rate limiting, logging redaction, and service failures in a staging environment.

## Commands
```bash
python3 -m pytest -q tests/test_day27_security.py tests/test_support_tools.py
python3 -m scripts.day27_demo
python3 -m pytest -q
```
