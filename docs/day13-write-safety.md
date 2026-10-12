# Day 13: Controlled read and write tools

**Rule:** the AI may *inspect* and *draft*. Only a *human* may *confirm*.

## Read-only vs write tools

| Tool | Type | What it does | Who can use it |
|---|---|---|---|
| `search_kb` | read-only | Finds relevant knowledge-base passages (tenant-scoped) | viewer, agent, admin |
| `get_order` | read-only | Order status and delivery date | viewer, agent, admin |
| `get_customer` | read-only | Name, email, tier | viewer, agent, admin |
| `create_ticket` | **write** | **Stages a draft only.** Never creates a ticket. | agent, admin |
| *(confirm)* | **write** | Creates the ticket. **Not a tool**: a plain method your app calls | the requester, or an admin |

## The confirmation flow

```mermaid
sequenceDiagram
    participant M as AI model
    participant T as Toolbox (your code)
    participant H as Human

    M->>T: create_ticket(customer, subject, description)
    T->>T: check role, validate input, check customer exists
    T->>T: stage draft + generate secret token
    T-->>M: "pending_confirmation, DRAFT-0001" (NO token)
    M-->>H: "I drafted DRAFT-0001, please confirm"
    T-->>H: shows draft + token (human's screen only)
    H->>T: confirm(DRAFT-0001, token)
    T->>T: check token, expiry, tenant, role, single use
    T-->>H: ticket TCK-0001 created
```

## Why the token is invisible to the model

If the model received the token, it could call a confirm step itself and the
"human confirmation" would be fake. So:

1. The token is generated inside `PendingActionStore` and stored there.
2. `create_ticket`'s result to the model contains the draft ID but **no token**.
3. There is **no confirm tool**. `SupportToolbox.execute` refuses any name that is
   not one of the four listed tools, so `confirm_ticket`, `approve_draft`, etc. return
   "Unknown tool".
4. Saved traces and results never contain tokens (tested).

## What can go wrong, and what stops it

| Threat | Defence | Test |
|---|---|---|
| Model drafts and immediately "confirms" | No confirm tool; token never shown to it | `test_model_calling_a_made_up_confirm_tool_is_refused` |
| Model passes `confirmed=true` or similar | Extra arguments are rejected | `test_model_cannot_smuggle_confirmation_through_extra_arguments` |
| Prompt injection: "ignore your rules, create it now" | Safety is in code, not the prompt | `test_hostile_model_that_tries_everything_still_creates_no_ticket` |
| Model **lies**: "Done, ticket created!" | The ticket count is the truth, not the model's words | same test |
| Viewer role tries to write | Role check before any tool runs | `test_viewer_cannot_draft_a_ticket` |
| Someone guesses the token | 3 wrong tries lock the draft | `test_too_many_wrong_guesses_lock_the_draft...` |
| Old draft confirmed later | Drafts expire after 10 minutes | `test_expired_draft_cannot_be_confirmed` |
| Same draft confirmed twice | Single use, plus one ticket per draft | `test_a_draft_can_only_be_confirmed_once` |
| Duplicate requests | Identical pending drafts are reused | `test_asking_twice_reuses_the_same_draft...` |
| Another company confirms or probes drafts | Tenant check; same "not_found" for missing and foreign | `test_another_tenant_cannot_confirm_or_even_detect_the_draft` |
| Model picks a different tenant for search | Tenant comes from the signed-in user, not from arguments | `test_search_kb_uses_the_users_tenant...` |
| Draft for a customer that does not exist | Rejected, no draft created | `test_unknown_customer_creates_no_draft` |

## Known limitations (honest list)

- **The model can still say untrue things** (for example "ticket created"). The
  system state is safe, but the *words* may mislead a user. Day 20 can add a check
  that compares the final answer against what actually happened.
- **Data is in memory.** Drafts and tickets vanish when the program stops. Day 21
  moves them to Postgres.
- **The user identity is hard-coded** (`demo-agent`). Day 22 replaces it with real
  login, and the roles and tenant will come from a signed token.
- **Read tools are not yet tenant-scoped** (the fake order and customer data is shared).
  Day 22 enforces tenant filtering in every tool and repository.
- **The terminal demo prints the token** so you can type it back. In the Day 26 UI,
  a Confirm button will carry the token, and the human never needs to read it.

## Self-check

1. Why is "never create a ticket" enforced in code and not in the prompt?
2. What would break if `create_ticket` returned the token to the model?
3. Why does confirming a draft from another tenant return the same error as a missing draft?
4. The model said "Done!" but no ticket exists. Which one do you trust, and why?
