# Day 11: Primitive vs. framework mapping

The Hugging Face Agents Course introduces agent concepts using a framework
(smolagents) that hides most of the loop behind a class like `CodeAgent` or
`ToolCallingAgent`. SupportPilot's Day 4 `run_agent` is the same idea, built
by hand. This table maps one to the other, concept by concept.

| Concept | Framework's name for it (e.g. smolagents) | Our raw version | File |
|---|---|---|---|
| The agent object | `CodeAgent(...)` / `ToolCallingAgent(...)` | `run_agent(task, ...)` function | `app/agent_loop.py` |
| Registering tools | `tools=[...]` passed to the agent | `tool_schemas` + `execute_tool` parameters | `app/agent_loop.py` |
| One tool | `@tool` decorated function | a plain Python function + a hand-written schema dict | `app/alfred_tools.py` |
| The think-act-observe cycle | hidden inside `agent.run(task)` | the `for step in range(1, max_steps + 1):` loop | `app/agent_loop.py` |
| Conversation history | managed internally by the framework | the `messages` list, built and passed explicitly | `app/agent_loop.py` |
| Step limit | `max_steps` argument to the framework agent | `MAX_STEPS` / `max_steps` parameter | `app/agent_loop.py` |
| Stopping safely | built-in, but not always visible | 3 explicit `stop_reason` values you can read | `app/agent_loop.py` |
| Swapping the model | change a config string | swap `chat_fn` for a different adapter | `app/model_adapter.py` (Day 5) |
| Debugging a run | framework-specific logging/tracing UI | `trace` list saved as plain JSON | `artifacts/day11_traces/` |

## What the framework buys you

- Less code to write for common patterns (one line to add a tool).
- Built-in integrations (web search, code execution sandboxes, hosted model APIs).
- A community-tested implementation, so subtle bugs in the loop itself are
  someone else's problem.
- Nicer developer experience: logging, tracing UIs, prompt templates.

## What it costs you

- You can't always see or change what happens inside the loop. If the
  framework handles duplicate-call detection differently than you'd like,
  you may not have access to change that.
- An opaque stop condition is harder to debug: Day 4's three `stop_reason`
  values are visible and testable (see `tests/test_agent.py`); a framework's
  internal equivalent might not be.
- Upgrading the framework can silently change agent behavior, since its
  internals are not in your control.
- Harder to explain in an interview: "the framework does it" is a weaker
  answer than being able to point at the exact loop and its stop conditions.

## When to reach for which

- **Learning, and anything where you need to explain or guarantee exact
  behavior** (like SupportPilot, which has to pass the Day 20 guardrail
  tests and the Day 27 security review): build the primitive yourself, or at
  least know exactly what a framework is doing underneath.
- **Shipping something quickly with standard needs** (a well-known tool like
  web search, a common agent pattern): a framework can be the faster, more
  maintained choice, once you understand what it's abstracting.

## The sprint's own rule on this

> "Do not add a new framework because a tutorial uses it. Learn the primitive first."

Day 11 and Day 12 are exactly this rule in practice: Day 11 proves you can
build and explain the primitive yourself (this file), and Day 12 (tomorrow)
will deliberately try a framework (smolagents) side by side with your own
loop, so the comparison is based on your own experience, not a guess.
