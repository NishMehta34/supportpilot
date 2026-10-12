# Day 22 — JWT authentication and tenant authorization

## Workbook goal
Local JWT auth, user/tenant/role claims, protected APIs, tenant isolation at API, tool and retrieval layers.

## Architecture
`/login` checks local credentials supplied to `create_app(users=...)` and issues short-lived HS256 JWTs. Every protected endpoint calls `current_principal` and uses verified JWT claims to scope repository operations. The ticket endpoint constructs `SupportToolbox(UserContext(...))` from the verified principal. No ticket confirmation route exists.

## Deliberate limitations
- **Development-only credential store:** cleartext demo passwords supplied to the app factory. Production requires hashed passwords and a proper identity provider.
- The default app has **no accounts**, so login is disabled until trusted bootstrap/configuration is supplied.
- Set a strong random `SUPPORTPILOT_JWT_SECRET` in the environment. Never commit it. JWT signatures and expiry are checked; no refresh tokens, revocation, rotation or rate limiting yet.
- Thread and document repositories remain **in-memory**; no real PostgreSQL tenant-row security is implemented.
- The Day 21 chat handler is still a placeholder. The Day 15 RAG retrieval layer and Day 18 MCP server are **not automatically secured by this API**. They must receive verified identity and enforce tenant-scoped queries independently before public deployment.
- No client-supplied tenant/user fields are trusted in protected routes. Extraneous JSON fields are ignored by Pydantic; a production contract may reject them instead.
- Access to documents is owner-scoped, not tenant-shared. Admin role is permitted to draft tickets, but not to read other users' private threads.
- CORS, HTTPS, CSRF/session concerns, account lockout, audit logging, user provisioning and token revocation are out of scope.

## Verification
`python3 -m pytest -q tests/test_day22_auth.py`; `python3 -m scripts.day22_demo`; `uvicorn app.day22_api:app --reload`.

## Production acceptance gap
The workbook requires isolation through **every endpoint and tool**. This package verifies the new Day 22 HTTP paths and toolbox identity construction, but does not prove isolation in the existing Day 15 retrieval queries or Day 18 MCP entry point. Do not claim full workbook completion until those paths are secured and tested.
