# Day 14 — Explicit LangGraph workflow

START → classify → retrieve → tool_decision → (answer | escalate) → END.

- `classify`: deterministic keyword routing, intentionally simple for Day 14.
- `retrieve`: calls Day 13 `search_kb` through the existing toolbox; failures are contained.
- `tool_decision`: selects a normal response or human escalation.
- `answer`: delegates to the existing bounded Day 13 support agent.
- `escalate`: returns a human-handoff message; it does not create a ticket.

## Security boundary
The graph never calls `toolbox.confirm`. The model only receives tool schemas from Day 13, which do not contain confirmation. Tokens must remain on the human side.

## Limitations
Classification is keyword-based and can miss nuanced requests. This is a workflow exercise, not a production-ready intent classifier. Retrieval is currently advisory: the existing support agent may retrieve again. No persistent checkpointing yet (Day 16). No actual escalation ticket is created. Avoid representing escalation as a completed human handoff.

## Acceptance
`pytest -q` and `python -m scripts.day14_demo` pass; `artifacts/day14.json` shows both routes.
