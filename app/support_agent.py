"""Day 13: SupportPilot agent v1.

A thin wrapper: our bounded Day 4 loop + the Day 13 toolbox + a support prompt.
The safety does NOT depend on this prompt. The prompt just helps the model
behave politely; the code in app/support_tools.py is what actually blocks writes.
"""

from app.agent_loop import run_agent
from app.tool_loop import ollama_chat

SUPPORT_SYSTEM_PROMPT = (
    "You are a customer support assistant for Nimbus Gadgets. Use the tools to look up "
    "orders, customers and the knowledge base. Only state facts that a tool returned; "
    "never invent data. If you need an ID you were not given, ask for it.\n"
    "You can DRAFT a support ticket with create_ticket, but drafting does not create it: "
    "a human must confirm the draft. After drafting, tell the user the draft ID and that "
    "it is waiting for their confirmation. Never say a ticket was created. Never ask for a "
    "confirmation code and never try to confirm a draft yourself; you cannot."
)


def run_support_agent(task, toolbox, chat_fn=ollama_chat, max_steps=6):
    """Run one support request for the user the toolbox was built for.

    The result has the usual fields (stop_reason, trace, final_answer, ...) plus
    `pending_drafts`: draft IDs waiting for confirmation. Tokens are deliberately
    NOT in the result, so they can never leak into a saved trace.
    """
    result = run_agent(
        task, chat_fn=chat_fn, max_steps=max_steps,
        tool_schemas=toolbox.schemas, execute_tool=toolbox.execute,
        system_prompt=SUPPORT_SYSTEM_PROMPT,
    )
    result["pending_drafts"] = [
        {"draft_id": d["draft_id"], "action": d["action"], "args": d["args"]}
        for d in toolbox.pending_for_review()
    ]
    return result
