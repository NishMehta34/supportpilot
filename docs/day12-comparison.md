# Day 12: Same agent, 3 ways

The same task (look up an order and its customer, using exactly 2 tools:
`get_order` and `get_customer`) built three times. Run each and fill in your
own real timings and observations.

## Run all three

```bash
python3 scripts/raw_version.py          # version 1: your raw Day 4/11 loop
pip install "smolagents[litellm]"       # one-time
python3 scripts/smolagents_version.py   # version 2: a real framework
python3 scripts/mini_agent_version.py   # version 3: your own tiny wrapper
```

## Comparison

| | Version 1: raw loop | Version 2: smolagents | Version 3: MiniAgent (ours) |
|---|---|---|---|
| File | `app/agent_loop.py` + `scripts/raw_version.py` | `scripts/smolagents_version.py` | `app/mini_agent.py` + `scripts/mini_agent_version.py` |
| Lines to define a tool | ~10 (hand-written schema dict) | ~8 (just a typed function + docstring) | same as version 1 (reuses the same schemas) |
| How the schema is built | you write the JSON by hand | generated from type hints + docstring | you write the JSON by hand |
| How the loop works | visible, in `run_agent`, ~40 lines you can read top to bottom | hidden inside `ToolCallingAgent.run()` | visible, `run_agent` underneath, just renamed |
| Step limit | `max_steps` parameter, your own code enforces it | `max_steps` parameter, framework enforces it internally | same as version 1 |
| Stuck-in-a-loop detection | explicit, yours, tested in `tests/test_agent.py` | not something you control directly | same as version 1 (inherited) |
| Swapping the model | swap `chat_fn` | swap the `model=` object (`LiteLLMModel`, `InferenceClientModel`, etc.) | swap `chat_fn` |
| Debugging a bad run | read `result["trace"]`, plain JSON | framework's own logging/telemetry | read `result["trace"]`, same as version 1 |
| New dependency | none (stdlib only) | `smolagents`, `litellm`, and their dependencies | none (stdlib only) |
| Time to first run (fill in) | | | |
| Lines of code you had to write (fill in) | | | |

## What I actually noticed (fill in after running all three)

1. **Which one was fastest to get a tool working?**

2. **Which one was easiest to debug when something went wrong?**
   (Try breaking something on purpose, like typing a wrong tool name, and
   see how each version reports the problem.)

3. **Which one would you trust more to explain to an interviewer, line by line?**

4. **What did smolagents give you "for free" that you'd have to build yourself?**

5. **What did smolagents hide that you could see clearly in your own version?**

## The actual decision for SupportPilot

SupportPilot keeps using the raw loop (`app/agent_loop.py`), not smolagents,
for the rest of this sprint. Here's why, concretely, not just as a rule to follow:

- Day 20 requires you to add specific guardrails (step budgets, timeouts,
  authorization checks) directly inside the loop. That's much easier when
  you wrote the loop.
- Day 27's security review needs you to reason precisely about what the
  agent can and cannot do. "The framework handles it" is a weaker answer
  than pointing at the exact line.
- The whole point of this sprint is to understand the primitive, not to
  collect framework experience for its own sake (see the sprint's own rule
  on this, quoted in `docs/day11-primitive-vs-framework.md`).

If this were a different kind of project, e.g. a prototype using several
pre-built tools (web search, code execution) where speed mattered more than
precise control, smolagents would be a reasonable choice instead.
