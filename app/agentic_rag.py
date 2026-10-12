"""Day 15: bounded agentic RAG, preserving Day 13's human-only confirmation.

Use build_agentic_rag_graph rather than modifying the Day 14 graph. All model
calls are injectable for offline testing; tool execution stays in SupportToolbox.
"""
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from typing import Any, TypedDict

from langgraph.graph import START, END, StateGraph

from app.support_agent import run_support_agent

ESCALATION_WORDS = ('human agent', 'supervisor', 'escalate', 'formal complaint')


class AgenticRAGState(TypedDict, total=False):
    task: str
    category: str
    route: str
    retrieval: dict[str, Any]
    agent_result: dict[str, Any]
    final_answer: str
    pending_drafts: list[dict[str, Any]]
    events: list[str]
    elapsed_ms: float
    failure: str | None


def _timed_call(fn, timeout_s):
    """Return result within a deadline; timeout does not cancel running thread.

    Never expose a timed-out tool's late result to the graph. True process-level
    cancellation and concurrency controls are deferred to Day 20.
    """
    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(fn)
    try:
        return future.result(timeout=timeout_s)
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def build_agentic_rag_graph(toolbox, chat_fn=None, *, max_steps=6,
                            tool_timeout_s=5.0, agent_timeout_s=30.0):
    """Compile a Day 15 graph with bounded delegated agent and fallbacks.

    Tool schemas are supplied by the Day 13 toolbox. `confirm` is never exposed.
    KB results are advisory; the agent must independently call search_kb for
    evidence it wants to cite. A timeout does not guarantee side-effect cancel.
    """
    if not 1 <= max_steps <= 6:
        raise ValueError('max_steps must be between 1 and 6')
    if tool_timeout_s <= 0 or agent_timeout_s <= 0:
        raise ValueError('timeouts must be positive')

    def classify(s):
        task = s['task'].lower()
        category = ('escalation' if any(w in task for w in ESCALATION_WORDS)
                    else 'ticket' if any(w in task for w in ('ticket', 'damaged', 'broken'))
                    else 'general')
        return {'category': category, 'events': ['classify']}

    def retrieve(s):
        try:
            result = _timed_call(lambda: toolbox.execute('search_kb', {'query': s['task']}),
                                 tool_timeout_s)
        except FutureTimeout:
            result = {'error': 'Knowledge-base lookup timed out'}
        except Exception:
            result = {'error': 'Knowledge-base lookup failed'}
        return {'retrieval': result, 'events': s['events'] + ['retrieve']}

    def decide(s):
        route = 'escalate' if s['category'] == 'escalation' else 'answer'
        return {'route': route, 'events': s['events'] + ['tool_decision']}

    def answer(s):
        start = time.perf_counter()
        try:
            kwargs = {'max_steps': max_steps}
            if chat_fn is not None:
                kwargs['chat_fn'] = chat_fn
            result = _timed_call(lambda: run_support_agent(s['task'], toolbox, **kwargs),
                                 agent_timeout_s)
            final = result.get('final_answer')
            failure = None
            if result.get('stop_reason') != 'final_answer' or not final:
                failure = result.get('stop_reason', 'empty_answer')
                final = 'I could not safely complete this request. Please contact support.'
            # Do not trust model claims about ticket creation: pending drafts are
            # application-owned and no ticket is created by this graph.
            drafts = [{'draft_id': d['draft_id'], 'action': d['action'], 'args': d['args']}
                      for d in result.get('pending_drafts', [])]
            if drafts:
                final = (f"Draft {drafts[-1]['draft_id']} is waiting for human confirmation. "
                         'No ticket has been created.')
            return {'agent_result': result, 'final_answer': final,
                    'pending_drafts': drafts, 'failure': failure,
                    'elapsed_ms': round((time.perf_counter()-start)*1000, 2),
                    'events': s['events'] + ['answer']}
        except FutureTimeout:
            error = 'agent_timeout'
        except Exception:
            error = 'agent_error'
        return {'final_answer': 'The assistant is temporarily unavailable. Please contact support.',
                'pending_drafts': [], 'failure': error,
                'elapsed_ms': round((time.perf_counter()-start)*1000, 2),
                'events': s['events'] + ['answer']}

    def escalate(s):
        return {'final_answer': 'A human support agent is needed. No ticket has been created.',
                'pending_drafts': [], 'failure': None,
                'events': s['events'] + ['escalate']}

    graph = StateGraph(AgenticRAGState)
    for name, node in [('classify', classify), ('retrieve', retrieve),
                       ('tool_decision', decide), ('answer', answer), ('escalate', escalate)]:
        graph.add_node(name, node)
    graph.add_edge(START, 'classify')
    graph.add_edge('classify', 'retrieve')
    graph.add_edge('retrieve', 'tool_decision')
    graph.add_conditional_edges('tool_decision', lambda s: s['route'],
                                {'answer': 'answer', 'escalate': 'escalate'})
    graph.add_edge('answer', END)
    graph.add_edge('escalate', END)
    return graph.compile()
