# Day 19 — Observability and debugging

## Architecture

`observe_run()` wraps any zero-argument support operation. It records a request ID, thread ID, model label, elapsed milliseconds, success/failure, exception class, and sanitized tool-step metadata. It logs JSON and can write a per-run JSON artifact. It returns the original result and re-raises the original exception.

## Wiring into SupportPilot

```python
from app.observability import observe_run
from app.agentic_rag import build_agentic_rag_graph

graph = build_agentic_rag_graph(toolbox, chat_fn=chat_fn)
result = observe_run(
    lambda: graph.invoke({'task': 'Where is ORD-1001?'}),
    thread_id='demo-thread', model='qwen3', artifact_dir='artifacts/day19-traces'
)
```

Use a server-generated request ID in the real API. `thread_id` must be a validated, authorized conversation ID, not an authentication mechanism.

## Trace schema

Each trace contains `request_id`, `thread_id`, `model`, `timestamp`, `success`, `latency_ms`, `error_type`, `tool`, `step_count`, and `steps`. Only recognized tool names and statuses are retained. No prompt, tool arguments, outputs, customer data, confirmation tokens, or raw exception messages are recorded. Some graph outputs have no `trace` list, so `steps` will be empty; graph-level node instrumentation is a future enhancement.

## Troubleshooting 10 runs

Run `python3 -m scripts.day19_demo` and inspect `artifacts/day19-report.json`. The demo intentionally produces two synthetic timeout failures so that the report can explain failures without rerunning them. The report is **not** a benchmark of the real Ollama model.

## Health endpoint

The existing `GET /health` endpoint in `app/main.py` returns `{'status':'ok'}`. It is a **liveness** response, not a readiness check of Postgres, Ollama, or pgvector. The Day 19 regression test checks this existing endpoint.

## Limitations and next steps

- The wrapper is opt-in: callers must use `observe_run()`; it is not automatically applied to every endpoint or node.
- Do not log secrets, raw exceptions, customer messages, or full tool payloads.
- Tool step names are available only if the operation returns a compatible `trace` list.
- Local JSON traces are not secured, rotated, or centrally aggregated; do not use this local storage for customer data.
- A timed-out operation may continue in the background (Day 15 limitation). Day 20 addresses execution budgets and timeout enforcement.
- Liveness is not readiness. Add dependency checks and metrics before production deployment.
