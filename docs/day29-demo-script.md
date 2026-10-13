# 3–5 minute SupportPilot demo — recording script

**Recording on Mac:** use QuickTime Player → File → New Screen Recording (or macOS Shift–Command–5). Record only a local demo; hide passwords, JWTs, API keys, personal data, and terminal history. Use test data.

| Time | Show | Suggested narration |
|---|---|---|
| 0:00–0:30 | README + problem | “SupportPilot explores evidence-backed customer support and safe ticket workflows.” |
| 0:30–1:10 | Architecture diagram | “The system has model/RAG/agent modules, an authenticated API and a browser UI. The live browser-to-agent integration remains open.” |
| 1:10–2:15 | Day 26 browser | “I log in locally, create a thread, send a message, and explain the placeholder chat response.” |
| 2:15–3:05 | Draft and confirm ticket | “The model can draft a ticket, but an authenticated human must explicitly confirm it.” |
| 3:05–3:45 | Terminal: tests | “I run the security and resilience suites and distinguish offline simulation from live readiness.” |
| 3:45–4:30 | Limitations + roadmap | “The main gaps are live agent integration, durable storage and end-to-end tenant isolation.” |

## Commands to prepare before recording
```bash
cd ~/Desktop/supportpilot
source .venv/bin/activate
python3 -m pytest -q tests/test_day27_security.py tests/test_day28_resilience.py
python3 -m scripts.day28_demo
```

For UI credentials, follow the local setup in `README-day29.md`. Start Uvicorn in another Terminal tab. If port 8001 is busy, check `lsof -nP -iTCP:8001 -sTCP:LISTEN` before changing it.

## Recording acceptance checklist
- [ ] Video is 3–5 minutes and audio is intelligible
- [ ] Demonstrates actual working browser ticket confirmation
- [ ] Clearly labels chat response as a placeholder
- [ ] Shows real test output, not invented metrics
- [ ] Mentions at least two concrete engineering trade-offs
- [ ] Does not expose credentials or private customer data
- [ ] Upload video to GitHub release, portfolio site, or a link you control; add its real URL to README
