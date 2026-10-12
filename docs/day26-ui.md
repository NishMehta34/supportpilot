# Day 26 — SupportPilot Browser Console

## Scope
The workbook calls for a simple UI with login, chat, citations, tool activity, threads, and human ticket confirmation. This is a framework-light, server-rendered HTML + vanilla JavaScript UI using the authenticated Day 22 API. The page is served at `/` and JS at `/day26.js`.

## Security boundaries
- JWT is kept in JavaScript memory only; refreshing logs out. No localStorage/sessionStorage token persistence.
- Text from API is rendered with `textContent`, never `innerHTML`.
- Strict CSP, no third-party scripts, no-store page headers.
- Authentication derives user and tenant from signed token; role checks on writes.
- Draft confirmation endpoint is **human-facing only** and calls `SupportToolbox.confirm`, never `execute`; tokens are shown to authenticated authorized users through `/ticket-drafts` and are not passed to the model.
- The UI uses an explicit browser confirmation dialog before sending the confirmation token.
- **No CSRF cookie risk** from token auth: browser doesn't attach bearer token automatically. Do not put tokens in URLs.

## Local-only demo
No demo accounts exist by default. Set `SUPPORTPILOT_DAY26_LOCAL_DEMO=1`, `SUPPORTPILOT_DAY26_DEMO_PASSWORD` (12+ chars) and a random 32+ character `SUPPORTPILOT_JWT_SECRET`. Bind Uvicorn to `127.0.0.1`. Demo mode is blocked when `SUPPORTPILOT_ENV=production`.

## Current limitations
- Day 21 chat service defaults to `configured: false`, so real model responses, citations and tool events are not available until an actual agent handler is injected. UI displays these fields if returned.
- No server-sent event streaming; uses a loading status while awaiting the full HTTP response.
- Day 21 in-memory repository, tickets and drafts are lost when the server restarts and are not suitable for multiple workers.
- Local plaintext demo account only; use a trusted identity provider and hashed password storage for real deployments.
- Day 13 order/customer lookup tools may not enforce tenant isolation. The UI does not expose these tools directly; audit all underlying tools before deploying.
- Confirmation tokens are returned to authorized browsers; avoid sensitive browser extensions and shared computers.
- UI lacks full accessibility review and browser automation; API integration tests validate the workflow, not pixel-perfect browser interactions.

## Run
```bash
python3 -m pip install 'PyJWT>=2.8,<3' fastapi httpx uvicorn pytest
export SUPPORTPILOT_JWT_SECRET="$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
export SUPPORTPILOT_DAY26_LOCAL_DEMO=1
export SUPPORTPILOT_DAY26_DEMO_PASSWORD="$(python3 -c 'import secrets; print(secrets.token_urlsafe(20))')"
printf 'Local demo username: demo-agent\\nPassword: %s\\n' "$SUPPORTPILOT_DAY26_DEMO_PASSWORD"
python3 -m pytest -q tests/test_day26_ui.py
python3 -m scripts.day26_demo
uvicorn app.day26_api:app --reload --host 127.0.0.1
```
Open http://127.0.0.1:8000/ and log in. Create thread, send message, create draft for CUS-001, refresh drafts and explicitly confirm. Check confirmed tickets. No model connection is claimed.
