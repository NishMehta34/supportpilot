# Day 20 — Guardrails, timeouts, retries, and execution budgets

## Architecture

`GuardedToolbox` wraps Day 13's `SupportToolbox.execute()` and retains its role checks, argument validation, and draft-only ticket behavior. `run_guarded_agent()` passes the guarded toolbox into the existing bounded Day 13 model loop. Use a new guard wrapper per request.

## Policies

| Control | Policy |
|---|---|
| Model steps | 1–6, enforced by existing agent loop |
| Tool calls | 8 per request by default; one logical call may include two read attempts |
| Input | 2,000 characters; tool argument budget 2,500 characters |
| Deadline | 30 seconds checked before each tool invocation and retry |
| Read timeout | 2 seconds waiting per read attempt |
| Read retry | Only explicit `temporarily_unavailable` error, maximum 2 attempts |
| Write retry | Never; write executes synchronously and exactly once per request |
| Authorization | Role check before dispatch, plus original toolbox checks |
| Confirmation | No `confirm_ticket` tool; only human-facing `SupportToolbox.confirm()` |

## Important limitations

A thread timeout stops waiting, **not execution**; the timed-out read can continue in the background. This design only wraps read-only tools in background threads. A blocking write can exceed the deadline because writes run synchronously; this avoids ambiguous background side effects but is not a hard execution deadline. A blocked model call can also exceed the budget; the step limit still applies. Hard cancellation requires isolated workers/processes and explicit cancellation/reconciliation semantics.

The Day 15 graph's existing `_timed_call()` still has separate timeout behavior. Integrating this wrapper into every graph node is a later refactor; Day 20's wrapper is exercised directly and through the Day 13 agent loop. Do not claim that all Day 15/16/17/18 execution paths are guarded yet.

Read tools in the original toolbox may still lack tenant authorization. This wrapper does not fix underlying row-level access; Day 22 must enforce verified identity and tenant-scoped repositories.

A malicious model can lie in its final answer; safety is based on toolbox state, not model text. Traces contain only event types and counters, not user input or tokens. Confirmed ticket writes are intentionally outside this guardrail wrapper.

## Evidence

Run `python3 -m pytest -q tests/test_guardrails.py`, then `python3 -m scripts.day20_demo`. Inspect `artifacts/day20-budget.json` and verify no `confirm_ticket` execution and that the tool budget is exhausted.
