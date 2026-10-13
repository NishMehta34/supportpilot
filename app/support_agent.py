
"""SupportPilot agent with retrieval grounding safeguards.

Uses the bounded agent loop and SupportToolbox.

Safety properties:
- Write operations remain protected by SupportToolbox.
- Ticket drafts require explicit human confirmation.
- KB citations must match retrieved document IDs.
- Invalid KB citation formats are rejected.
- KB answers without retrieved evidence are blocked when a search occurred.

Note:
Retrieved evidence alone does not establish factual correctness.
"""

import re

from app.agent_loop import run_agent
from app.tool_loop import ollama_chat


SUPPORT_SYSTEM_PROMPT = (
    "You are a customer support assistant for Nimbus Gadgets. "
    "Use the tools to look up orders, customers and the knowledge base. "
    "Only state facts that a tool returned; never invent data. "
    "If you need an ID you were not given, ask for it.\n"

    "You can DRAFT a support ticket with create_ticket, but drafting "
    "does not create it: a human must confirm the draft. "
    "After drafting, tell the user the draft ID and that it is waiting "
    "for their confirmation. Never say a ticket was created. "
    "Never ask for a confirmation code and never try to confirm "
    "a draft yourself; you cannot.\n"

    "For questions about policies, prices, shipping, warranties, "
    "returns, products, and troubleshooting, call search_kb before "
    "answering. Do not answer these questions from memory.\n"

    "When answering from search_kb results, cite source document IDs "
    "using the exact format [KB-DOCUMENT-ID]. "
    "Put section names outside the citation brackets. "
    "For example: According to the 'Return window' section "
    "[KB-RETURNS], Standard members have 30 days to return an item. "
    "Never write citations like [KB-RETURNS > Return window]. "
    "Only cite document IDs that actually appeared in tool results.\n"

    "When answering policy questions, identify the exact policy "
    "section that answers the user's question. "
    "Do not confuse general return windows with damaged-item "
    "reporting deadlines. "
    "Quote or accurately paraphrase the relevant policy detail. "
    "If the retrieved passages do not contain the answer, "
    "say that the information could not be verified."
)


UNVERIFIED_ANSWER = (
    "I couldn't verify that information from the available "
    "knowledge base. Please contact support for confirmation."
)


# Valid examples:
# [KB-RETURNS]
# [KB-WARRANTY]
# [KB-TROUBLESHOOT]
KB_CITATION_PATTERN = re.compile(
    r"\[(KB-[A-Za-z0-9_-]+)\]"
)


# Invalid examples:
# [KB-WARRANTY > Replacement process]
# [KB-TROUBLESHOOT > Hub: no display on the monitor]
INVALID_KB_CITATION_PATTERN = re.compile(
    r"\[KB-[A-Za-z0-9_-]+\s*>[^\]]+\]"
)


def _collect_search_results(value, found):
    """Collect document IDs from recorded search result objects."""
    if isinstance(value, dict):

        if isinstance(value.get("results"), list):
            for item in value["results"]:
                if isinstance(item, dict):
                    doc_id = item.get("doc_id")

                    if isinstance(doc_id, str) and doc_id:
                        found.add(doc_id)

        for key, nested in value.items():
            if key != "results" and isinstance(nested, (dict, list)):
                _collect_search_results(nested, found)

    elif isinstance(value, list):
        for item in value:
            _collect_search_results(item, found)


def _get_trace_tool_name(entry):
    """Extract a tool name from common trace structures."""
    if not isinstance(entry, dict):
        return None

    for key in ("tool", "tool_name", "name"):
        value = entry.get(key)

        if isinstance(value, str):
            return value

    tool_call = entry.get("tool_call")

    if isinstance(tool_call, dict):
        function = tool_call.get("function")

        if isinstance(function, dict):
            return function.get("name")

        return tool_call.get("name")

    return None


def _trace_has_kb_search(trace):
    """Determine whether the agent attempted a KB search."""
    for entry in trace:

        if _get_trace_tool_name(entry) == "search_kb":
            return True

        if isinstance(entry, dict):
            calls = entry.get("tool_calls")

            if isinstance(calls, list):
                for call in calls:
                    if _get_trace_tool_name(call) == "search_kb":
                        return True

    return False


def enforce_retrieval_grounding(result):
    """Validate KB citation formatting and retrieved evidence.

    Checks:
    1. Reject section-qualified KB citations.
    2. Reject citations for documents not retrieved.
    3. Reject KB answers when a search returned no evidence.

    This is not a semantic factual-accuracy evaluator.
    """
    trace = result.get("trace") or []
    answer = result.get("final_answer")

    if not isinstance(answer, str):
        result["grounding_status"] = "not_applicable"
        return result

    retrieved_docs = set()
    _collect_search_results(trace, retrieved_docs)

    result["retrieved_kb_doc_ids"] = sorted(retrieved_docs)

    # 1. Reject malformed section-qualified citations.
    if INVALID_KB_CITATION_PATTERN.search(answer):
        result["final_answer"] = UNVERIFIED_ANSWER
        result["grounding_status"] = "invalid_citation_format"
        result["cited_kb_doc_ids"] = []
        return result

    # 2. Extract valid KB citations.
    cited_docs = set(
        KB_CITATION_PATTERN.findall(answer)
    )

    result["cited_kb_doc_ids"] = sorted(cited_docs)

    # 3. Reject citations absent from retrieved documents.
    unsupported_citations = cited_docs - retrieved_docs

    if unsupported_citations:
        result["final_answer"] = UNVERIFIED_ANSWER
        result["grounding_status"] = "unsupported_citation"
        result["unsupported_citations"] = sorted(
            unsupported_citations
        )
        return result

    # 4. Reject an answer when KB search produced no evidence.
    searched_kb = _trace_has_kb_search(trace)

    if searched_kb and not retrieved_docs:
        result["final_answer"] = UNVERIFIED_ANSWER
        result["grounding_status"] = "no_evidence"
        return result

    # 5. Record the evidence state.
    if retrieved_docs:
        result["grounding_status"] = "evidence_retrieved"
    else:
        result["grounding_status"] = "not_applicable"

    return result


def run_support_agent(
    task,
    toolbox,
    chat_fn=ollama_chat,
    max_steps=6,
):
    """Run a support request using the tenant-scoped toolbox.

    The result includes:
    - stop_reason
    - trace
    - final_answer
    - grounding_status
    - retrieved_kb_doc_ids
    - cited_kb_doc_ids
    - pending_drafts

    Confirmation tokens are deliberately excluded.
    """
    result = run_agent(
        task,
        chat_fn=chat_fn,
        max_steps=max_steps,
        tool_schemas=toolbox.schemas,
        execute_tool=toolbox.execute,
        system_prompt=SUPPORT_SYSTEM_PROMPT,
    )

    # Apply KB grounding safeguards.
    result = enforce_retrieval_grounding(result)

    # Keep the human-confirmation workflow unchanged.
    result["pending_drafts"] = [
        {
            "draft_id": draft["draft_id"],
            "action": draft["action"],
            "args": draft["args"],
        }
        for draft in toolbox.pending_for_review()
    ]

    return result
