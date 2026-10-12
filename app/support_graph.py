"""Day 14: explicit support workflow; no confirmation capability in the graph."""
from typing import TypedDict, Any
from langgraph.graph import StateGraph, START, END
from app.support_agent import run_support_agent

ESCALATION_WORDS = ('human agent', 'supervisor', 'escalate', 'formal complaint')

class SupportState(TypedDict, total=False):
    task: str
    category: str
    retrieval: dict[str, Any]
    route: str
    final_answer: str
    agent_result: dict[str, Any]
    pending_drafts: list[dict[str, Any]]
    events: list[str]


def build_support_graph(toolbox, chat_fn=None):
    """Compile a fresh graph using the existing Day 13 toolbox.

    The model can use only toolbox.schemas/execute; human confirmation stays
    outside this graph. Retrieval is advisory; failures don't crash routing.
    """
    def classify(state):
        task = state['task'].lower()
        category = ('escalation' if any(s in task for s in ESCALATION_WORDS)
                    else 'ticket' if any(s in task for s in ('ticket', 'damaged', 'broken'))
                    else 'general')
        return {'category': category, 'events': ['classify']}

    def retrieve(state):
        result = toolbox.execute('search_kb', {'query': state['task']})
        return {'retrieval': result, 'events': state['events'] + ['retrieve']}

    def decide(state):
        route = 'escalate' if state['category'] == 'escalation' else 'answer'
        return {'route': route, 'events': state['events'] + ['tool_decision']}

    def answer(state):
        kwargs = {'chat_fn': chat_fn} if chat_fn is not None else {}
        result = run_support_agent(state['task'], toolbox, **kwargs)
        return {'agent_result': result, 'final_answer': result.get('final_answer') or
                'Unable to complete this request automatically.',
                'pending_drafts': result['pending_drafts'],
                'events': state['events'] + ['answer']}

    def escalate(state):
        return {'final_answer': 'This request needs a human support agent. No ticket has been created.',
                'pending_drafts': [], 'events': state['events'] + ['escalate']}

    graph = StateGraph(SupportState)
    graph.add_node('classify', classify)
    graph.add_node('retrieve', retrieve)
    graph.add_node('tool_decision', decide)
    graph.add_node('answer', answer)
    graph.add_node('escalate', escalate)
    graph.add_edge(START, 'classify')
    graph.add_edge('classify', 'retrieve')
    graph.add_edge('retrieve', 'tool_decision')
    graph.add_conditional_edges('tool_decision', lambda s: s['route'],
                                {'answer': 'answer', 'escalate': 'escalate'})
    graph.add_edge('answer', END)
    graph.add_edge('escalate', END)
    return graph.compile()
