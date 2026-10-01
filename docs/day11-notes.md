# Day 11: Agent fundamentals, in my own words

*Read the Hugging Face Agents Course syllabus, Unit 1 ("Introduction to Agents"),
and "What is an Agent?" first. This page is a scaffold, fill in anything
marked (your words) after you've done the reading and built alfred_demo.py.*

## What is an agent?

An agent is a system where a **language model decides what to do next**, and
a program carries that decision out. The model is the brain; it never touches
a database, a file, or the internet directly. It only ever produces text
saying what it wants done. Everything that actually *happens* is done by
ordinary code that the model has no control over except through its requests.

(your words: why does keeping "decide" and "do" as two separate things matter for safety?)

## Think, Act, Observe

Every agent, however it's built, repeats the same three-part cycle:

1. **Think** — the model looks at everything so far and decides the next move.
2. **Act** — the chosen tool actually runs. This step belongs to your code, never the model.
3. **Observe** — the model reads the result and starts the cycle again, or stops.

This is precisely the loop built in Day 4's `app/agent_loop.py`, and reused
unchanged for Alfred in `scripts/alfred_demo.py`.

(your words: pick one trace from `artifacts/day11_traces/` and label each step as Think, Act, or Observe)

## The model as "the brain"

The model has no memory between calls and cannot act on its own. Every single
time it's asked something, it is handed the *entire* conversation so far
(every past tool result included) and asked "given all of this, what now?"
This is why `messages` keeps growing throughout `run_agent`, each pass adds
to it rather than replacing it.

(your words: what would happen if you only sent the model the latest message, not the whole history?)

## Tools, schemas, and messages

- A **tool** is just a normal Python function (`check_weather`, `get_order`, `calculator`).
- A **schema** is a short description of a tool the model gets to read: its
  name, what it does, and what arguments it takes. The model never sees the
  function's code, only this description.
- A **message** is one turn in the conversation: `system` (the rules), `user`
  (the question), `assistant` (the model's reply, possibly a tool request),
  or `tool` (a result handed back).

(your words: why can't the model just call `get_order("ORD-1001")` directly, the way your own Python code can?)

## Bounded autonomy

An agent that can act repeatedly can also act forever. Day 4 and Day 11 both
enforce the same two guards regardless of which tools are in play:
- a hard step limit (`max_steps`)
- detection of the agent repeating an identical request

(your words: why is this a property of the LOOP, not of any individual tool?)

## My own diagram

See `docs/day11-state-diagram.md` for the state machine. Trace one real run
from `artifacts/day11_traces/` against it and confirm every step matches a
state in the diagram, with nothing left unexplained.
