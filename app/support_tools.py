"""Day 13: SupportPilot's business tools, split into READ-ONLY and WRITE.

The one rule that shapes everything in this file:

    The AI may INSPECT and DRAFT. Only a HUMAN may CONFIRM.

How that is enforced (in code, not in the prompt):
  * create_ticket does not create anything. It only stages a draft.
  * The confirmation token is generated here and is shown to the human only.
    It is never put into a tool result, so the model never sees it.
  * There is no tool the model can call to confirm. Confirmation is a plain
    Python method (SupportToolbox.confirm) called by your app / UI.
"""

import secrets
import time
from dataclasses import dataclass, field

from app.tools import get_customer, get_order, normalize_id

READ_ONLY_TOOLS = ("search_kb", "get_order", "get_customer")
WRITE_TOOLS = ("create_ticket",)

WRITE_ROLES = ("agent", "admin")           # who may draft and confirm tickets
KNOWN_ROLES = ("viewer", "agent", "admin")

CONFIRMATION_TTL_SECONDS = 600             # a draft expires after 10 minutes
MAX_TOKEN_ATTEMPTS = 3                     # then the draft is locked (cancelled)
KB_MIN_SCORE = 0.35                        # ignore weak knowledge-base matches
KB_RESULTS = 3

MAX_SUBJECT = 120
MAX_DESCRIPTION = 2000


@dataclass(frozen=True)
class UserContext:
    """Who is making the request. Comes from login (Day 22), never from the model."""
    user_id: str
    tenant_id: str
    role: str


@dataclass
class PendingAction:
    draft_id: str
    action: str
    args: dict
    tenant_id: str
    requested_by: str
    token: str
    created_at: float
    expires_at: float
    status: str = "pending"                # pending | confirmed | cancelled | expired
    failed_attempts: int = 0


class PendingActionStore:
    """Holds drafts that are waiting for a human to confirm them."""

    def __init__(self, now_fn=time.time, token_fn=None, ttl=CONFIRMATION_TTL_SECONDS):
        self._items = {}
        self._now = now_fn
        self._token_fn = token_fn or (lambda: secrets.token_hex(4))   # e.g. "9f3a1c7e"
        self._ttl = ttl
        self._counter = 0

    def stage(self, action, args, ctx):
        """Create a draft. Returns (item, is_new). An identical draft that is still
        pending is reused, so repeating a request never creates duplicates."""
        now = self._now()
        for item in self._items.values():
            if (item.status == "pending" and item.action == action and item.args == args
                    and item.tenant_id == ctx.tenant_id and item.requested_by == ctx.user_id
                    and item.expires_at > now):
                return item, False

        self._counter += 1
        item = PendingAction(
            draft_id=f"DRAFT-{self._counter:04d}", action=action, args=dict(args),
            tenant_id=ctx.tenant_id, requested_by=ctx.user_id, token=self._token_fn(),
            created_at=now, expires_at=now + self._ttl,
        )
        self._items[item.draft_id] = item
        return item, True

    def get(self, draft_id):
        return self._items.get(draft_id)

    def pending_for(self, ctx):
        now = self._now()
        return [i for i in self._items.values()
                if i.tenant_id == ctx.tenant_id and i.status == "pending" and i.expires_at > now
                and (i.requested_by == ctx.user_id or ctx.role == "admin")]

    def confirm(self, draft_id, token, ctx):
        """Validate a human's confirmation. Returns {"ok": True, "item": ...} or
        {"ok": False, "error": <code>}. Never raises."""
        item = self._items.get(draft_id)
        # Same answer for "missing" and "belongs to another tenant": no information leak.
        if item is None or item.tenant_id != ctx.tenant_id:
            return {"ok": False, "error": "not_found"}
        if ctx.role not in WRITE_ROLES:
            return {"ok": False, "error": "permission_denied"}
        if item.requested_by != ctx.user_id and ctx.role != "admin":
            return {"ok": False, "error": "permission_denied"}
        if item.status != "pending":
            return {"ok": False, "error": f"already_{item.status}"}
        if self._now() >= item.expires_at:
            item.status = "expired"
            return {"ok": False, "error": "expired"}

        if not secrets.compare_digest(str(token or ""), item.token):
            item.failed_attempts += 1
            if item.failed_attempts >= MAX_TOKEN_ATTEMPTS:
                item.status = "cancelled"
                return {"ok": False, "error": "locked_too_many_attempts"}
            return {"ok": False, "error": "wrong_token"}

        item.status = "confirmed"            # single use: it can never be confirmed again
        return {"ok": True, "item": item}

    def cancel(self, draft_id, ctx):
        item = self._items.get(draft_id)
        if item is None or item.tenant_id != ctx.tenant_id:
            return {"ok": False, "error": "not_found"}
        if item.status != "pending":
            return {"ok": False, "error": f"already_{item.status}"}
        item.status = "cancelled"
        return {"ok": True}


class TicketStore:
    """Where real tickets live. In-memory for now; Day 21 moves this to Postgres."""

    def __init__(self):
        self._tickets = []

    def create(self, tenant_id, customer_id, subject, description, created_by, draft_id):
        for ticket in self._tickets:           # idempotent: one ticket per draft, ever
            if ticket["draft_id"] == draft_id:
                return ticket
        ticket = {
            "ticket_id": f"TCK-{len(self._tickets) + 1:04d}", "tenant_id": tenant_id,
            "customer_id": customer_id, "subject": subject, "description": description,
            "created_by": created_by, "draft_id": draft_id, "status": "open",
        }
        self._tickets.append(ticket)
        return ticket

    def all(self):
        return list(self._tickets)

    def count(self):
        return len(self._tickets)


def _schema(name, description, properties, required):
    return {"type": "function", "function": {
        "name": name, "description": description,
        "parameters": {"type": "object", "properties": properties, "required": required}}}


def _string(description):
    return {"type": "string", "description": description}


SUPPORT_TOOL_SCHEMAS = [
    _schema("search_kb", "READ-ONLY. Search the support knowledge base (policies, warranty, "
            "shipping, troubleshooting) and return the most relevant passages.",
            {"query": _string("What to look up, in plain words")}, ["query"]),
    _schema("get_order", "READ-ONLY. Look up an order's status and delivery date by order ID.",
            {"order_id": _string("e.g. ORD-1001")}, ["order_id"]),
    _schema("get_customer", "READ-ONLY. Look up a customer's name, email and tier by customer ID.",
            {"customer_id": _string("e.g. CUS-001")}, ["customer_id"]),
    _schema("create_ticket", "WRITE (needs human confirmation). Draft a support ticket. This does "
            "NOT create the ticket; it stages a draft that a human must confirm.",
            {"customer_id": _string("e.g. CUS-001"),
             "subject": _string("Short title of the problem"),
             "description": _string("What happened, in a few sentences")},
            ["customer_id", "subject", "description"]),
]


class SupportToolbox:
    """Everything the support agent is allowed to do, for ONE signed-in user."""

    def __init__(self, ctx, retrieve_fn, pending_store=None, ticket_store=None):
        self.ctx = ctx
        self._retrieve = retrieve_fn
        self.pending = pending_store or PendingActionStore()
        self.tickets = ticket_store or TicketStore()

    @property
    def schemas(self):
        return SUPPORT_TOOL_SCHEMAS

    # ------------------------------------------------------------------
    # What the MODEL can reach: execute() only. It never raises.
    # ------------------------------------------------------------------
    def execute(self, name, arguments):
        if name not in READ_ONLY_TOOLS + WRITE_TOOLS:
            return {"error": f"Unknown tool: {name}"}
        if not isinstance(arguments, dict):
            return {"error": f"Invalid arguments for {name}"}
        if self.ctx.role not in KNOWN_ROLES:
            return {"error": "permission_denied: unknown role"}
        if name in WRITE_TOOLS and self.ctx.role not in WRITE_ROLES:
            return {"error": f"permission_denied: role '{self.ctx.role}' cannot use {name}"}
        try:
            return getattr(self, f"_tool_{name}")(**arguments)
        except TypeError as error:           # wrong or extra arguments (e.g. confirmed=True)
            return {"error": f"Invalid arguments for {name}: {error}"}
        except Exception as error:           # a broken tool must never crash the agent
            return {"error": f"Tool {name} failed: {error}"}

    def _tool_search_kb(self, query):
        if not isinstance(query, str) or not query.strip():
            return {"error": "query must be a non-empty string"}
        if len(query) > 500:
            return {"error": "query too long"}
        try:
            # The tenant comes from the signed-in user, never from the model.
            chunks = self._retrieve(query.strip(), self.ctx.tenant_id, KB_RESULTS)
        except Exception:
            return {"error": "Knowledge base unavailable right now"}
        good = [c for c in chunks if c.get("score", 0) >= KB_MIN_SCORE]
        if not good:
            return {"results": [], "note": "No relevant knowledge-base passage found"}
        return {"results": [{"doc_id": c["doc_id"], "section": c["section"],
                             "snippet": c["content"][:300], "score": round(c["score"], 3)}
                            for c in good]}

    def _tool_get_order(self, order_id):
        return get_order(order_id)

    def _tool_get_customer(self, customer_id):
        return get_customer(customer_id)

    def _tool_create_ticket(self, customer_id, subject, description):
        if not all(isinstance(v, str) for v in (customer_id, subject, description)):
            return {"error": "customer_id, subject and description must be text"}
        subject, description = subject.strip(), description.strip()
        if not 1 <= len(subject) <= MAX_SUBJECT:
            return {"error": f"subject must be 1-{MAX_SUBJECT} characters"}
        if not 1 <= len(description) <= MAX_DESCRIPTION:
            return {"error": f"description must be 1-{MAX_DESCRIPTION} characters"}

        customer_id = normalize_id(customer_id)
        if "error" in get_customer(customer_id):
            return {"error": f"Customer {customer_id} not found; no draft was created"}

        args = {"customer_id": customer_id, "subject": subject, "description": description}
        item, is_new = self.pending.stage("create_ticket", args, self.ctx)
        # NOTE: no token in this result. The model must never see it.
        return {
            "status": "pending_confirmation", "draft_id": item.draft_id,
            "duplicate_of_existing_draft": not is_new,
            "message": "Draft staged. NO ticket has been created. A human must confirm "
                       "it first. Tell the user the draft ID and that it is waiting for them.",
        }

    # ------------------------------------------------------------------
    # What only a HUMAN / your app can reach. Not listed in the schemas, and
    # execute() refuses any name outside READ_ONLY_TOOLS + WRITE_TOOLS.
    # ------------------------------------------------------------------
    def pending_for_review(self):
        """Drafts waiting for this user, WITH tokens. For the human's screen only."""
        return [{"draft_id": i.draft_id, "action": i.action, "args": i.args, "token": i.token}
                for i in self.pending.pending_for(self.ctx)]

    def confirm(self, draft_id, token):
        outcome = self.pending.confirm(draft_id, token, self.ctx)
        if not outcome["ok"]:
            return outcome
        item = outcome["item"]
        ticket = self.tickets.create(
            tenant_id=item.tenant_id, customer_id=item.args["customer_id"],
            subject=item.args["subject"], description=item.args["description"],
            created_by=item.requested_by, draft_id=item.draft_id,
        )
        return {"ok": True, "ticket": ticket}

    def cancel(self, draft_id):
        return self.pending.cancel(draft_id, self.ctx)
