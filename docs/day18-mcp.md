# Day 18 — SupportPilot MCP server

## Purpose

The MCP server exposes three existing Day 13 capabilities through the official Python MCP SDK: `get_order`, `search_kb`, and `create_ticket`. It reuses `SupportToolbox.execute`, so native tools and MCP tools share the same permission checks and input validation. The workbook references the TypeScript SDK v2 for learning, but this Python code uses the official Python SDK because SupportPilot is a Python application.

## Host, client, server

- **Host**: an application that wants access to tools (e.g. a desktop AI application).
- **Client**: the protocol connection within that application; `scripts/day18_mcp_client.py` is a standalone example.
- **Server**: `app/mcp_server.py`, exposing business tools via MCP over stdio.

## Tools and schemas

| Tool | Arguments | Result | Side effects |
|---|---|---|---|
| `get_order` | `order_id: str` | JSON order or error | Read-only |
| `search_kb` | `query: str` | JSON relevant passages or no matches | Read-only |
| `create_ticket` | `customer_id: str`, `subject: str`, `description: str` | JSON draft ID, pending confirmation | Stages draft only |

No `confirm_ticket` tool exists. The human-only `SupportToolbox.confirm` method is never exposed to the MCP client. Confirmation tokens are never returned in tool results.

## Local setup (macOS)

```bash
python3 -m pip install 'mcp>=1,<2'
python3 -m pytest -q tests/test_mcp_server.py
python3 -m scripts.day18_mcp_client
```

The client launches the server as a subprocess, discovers its tools, invokes all three, and writes `artifacts/day18.json`. Stdio transports protocol frames on stdout: don't add `print()` statements to server startup.

## MCP vs native

Native: `toolbox.execute('get_order', {'order_id': 'ORD-1001'})`.

MCP: `await session.call_tool('get_order', {'order_id': 'ORD-1001'})`.

Both use the same business dispatcher. MCP wraps results as content blocks; this demo encodes business results as JSON text.

## Known limitations — important

1. **Demo identity only.** The stdio server takes identity from its trusted launch environment. It has no remote authentication. Never expose it over HTTP without verified identity and per-tool authorization.
2. **Order read isolation is incomplete.** Day 13's `get_order` does not yet enforce tenant ownership. Do not use this with real multi-tenant customer records until fixed.
3. **Knowledge-base search is a stub in the default launcher.** It returns no matches. The adapter accepts `retrieve_fn` for connecting the Day 9 pgvector retriever; a live KB integration is a separate acceptance step.
4. **Pending drafts are in-memory.** The demo client and server process end together, so a staged draft cannot be confirmed after process exit. A production app needs shared durable pending-action storage and a separate authenticated human confirmation UI.
5. **No resources or prompts exposed.** Today's workbook specifically asks for tools; learn how resources and prompts differ but do not add unnecessary endpoints.
6. **No user-supplied tenant identity.** MCP tool schemas do not accept `tenant_id` or `role`. The server constructs a trusted toolbox at startup. Production must verify these claims via authentication.

## Acceptance

- MCP client lists exactly three tools.
- Client calls each tool successfully.
- `create_ticket` returns a draft, not a ticket.
- No confirmation token or confirmation tool reaches the client.
- Existing Day 13 tests continue passing.
- Live pgvector-backed `search_kb` remains to be wired for full feature parity.
