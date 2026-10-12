"""Day 16: restart-safe conversation state around the Day 15 agent.

Local SQLite checkpoints are for development, not a multi-user production store.
Never put human confirmation tokens into this graph's state.
"""
import re
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import TypedDict

from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.sqlite import SqliteSaver

from app.agentic_rag import build_agentic_rag_graph

ORDER_ID = re.compile(r'\bORD-\d+\b', re.IGNORECASE)
MAX_HISTORY = 12


class ConversationState(TypedDict, total=False):
    question: str
    history: list[dict[str, str]]
    last_order_id: str | None
    resolved_question: str
    final_answer: str
    route: str
    failure: str | None
    events: list[str]


def build_conversation_graph(toolbox, chat_fn=None, **agent_options):
    """Build graph; caller compiles with a persistent checkpointer."""
    day15 = build_agentic_rag_graph(toolbox, chat_fn=chat_fn, **agent_options)

    def respond(state: ConversationState):
        question = state['question'].strip()
        if not question:
            raise ValueError('question must not be empty')
        previous_id = state.get('last_order_id')
        match = ORDER_ID.search(question)
        order_id = match.group(0).upper() if match else previous_id
        # Explicit, narrow context resolution: do not invent other user facts.
        refers_to_order = bool(re.search(r'\b(it|that order|this order|the order)\b', question, re.I))
        resolved = (question + f' (referring to order {order_id})'
                    if not match and order_id and refers_to_order else question)
        result = day15.invoke({'task': resolved})
        answer = result.get('final_answer', 'Support is unavailable.')
        # Persist only plain conversation turns, not model traces, tool responses,
        # pending drafts or secret confirmation tokens.
        history = (state.get('history') or []) + [
            {'role': 'user', 'content': question},
            {'role': 'assistant', 'content': answer},
        ]
        return {'history': history[-MAX_HISTORY:], 'last_order_id': order_id,
                'resolved_question': resolved, 'final_answer': answer,
                'route': result.get('route', 'unknown'),
                'failure': result.get('failure'),
                'events': result.get('events', [])}

    graph = StateGraph(ConversationState)
    graph.add_node('respond', respond)
    graph.add_edge(START, 'respond')
    graph.add_edge('respond', END)
    return graph


@contextmanager
def open_conversation_graph(db_path, toolbox, chat_fn=None, **agent_options):
    """Keep the SQLite connection open for the graph's lifetime."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path), check_same_thread=False)
    try:
        saver = SqliteSaver(connection)
        yield build_conversation_graph(toolbox, chat_fn, **agent_options).compile(checkpointer=saver)
    finally:
        connection.close()


def thread_config(thread_id: str, tenant_id: str, user_id: str):
    """Build a collision-free checkpoint key from trusted identity values.

    LangGraph SQLite identifies conversation histories primarily by thread_id.
    Do not rely on checkpoint_ns alone for tenant/user isolation.
    """
    if not all(isinstance(x, str) and x.strip() for x in (thread_id, tenant_id, user_id)):
        raise ValueError('thread_id, tenant_id and user_id are required')
    internal_id = json.dumps([tenant_id, user_id, thread_id], separators=(',', ':'), ensure_ascii=True)
    return {'configurable': {
        'thread_id': internal_id,
        'checkpoint_ns': '',
    }}
