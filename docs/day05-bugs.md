# Day 5: Bugs reproduced and fixed

Method for every bug: **write a failing test first (red) -> fix the code -> rerun (green).**

## Bug 1: Valid answers rejected because the model wrapped them in extra text
- **Symptom:** The classifier rejected answers that were actually correct, e.g. JSON inside a
  ```json code fence, after a `<think>...</think>` block, or after a chatty "Sure! Here it is:".
- **Cause:** We handed the raw model text straight to the validator, which expects pure JSON.
- **Fix:** `app/json_cleanup.py` pulls the JSON out of the text *before* validation. The strict
  validation still runs afterwards, so bad values are still blocked.
- **Regression tests:** `tests/test_regressions.py` -> `test_bug1_*`
- **What I saw when I ran it (paste the failing pytest lines here):**

## Bug 2: A malformed tool call crashed the loops
- **Symptom:** If the model requested a tool without "arguments", a name, or a "function", the app
  crashed with a KeyError instead of handling it.
- **Cause:** Both loops assumed every tool call was perfectly formed.
- **Fix:** `app/tool_calls.py` has one safe `parse_tool_call` used by both loops. A malformed call
  becomes an error result that is handed back to the model.
- **Regression tests:** `tests/test_regressions.py` -> `test_bug2_*`
- **What I saw when I ran it (paste the failing pytest lines here):**

## Bug 3: `ord-1001` was "not found" but `ORD-1001` worked
- **Symptom:** Lookups failed when the model changed capitalisation or added a space, and
  `search_orders(status="Processing")` found nothing.
- **Cause:** Exact string matching on IDs and statuses.
- **Fix:** IDs are trimmed and upper-cased, statuses trimmed and lower-cased, before lookup.
- **Regression tests:** `tests/test_regressions.py` -> `test_bug3_*`
- **What I saw when I ran it (paste the failing pytest lines here):**

## Lessons
1. Models are polite but messy: never assume their output is perfectly shaped.
2. A bug fixed without a test can come back. A bug fixed with a test cannot.
3. Guard tests (like "plain text is still rejected") make sure a fix does not make the app too lenient.
