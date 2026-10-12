import pytest
from app.conversation_memory import open_conversation_graph, thread_config
from app.support_tools import SupportToolbox, UserContext


def make_toolbox():
    return SupportToolbox(UserContext('u1', 'tenant1', 'agent'),
                          retrieve_fn=lambda q, tenant, k: [])


def model(messages, schemas):
    return {'role': 'assistant', 'content': 'Order assistance available.'}


def config(thread='A', tenant='tenant1', user='u1'):
    return thread_config(thread, tenant, user)


def test_dependent_turn_and_restart(tmp_path):
    path = tmp_path / 'checkpoints.sqlite'
    with open_conversation_graph(path, make_toolbox(), model) as graph:
        first = graph.invoke({'question': 'Check ORD-1001'}, config=config())
        assert first['last_order_id'] == 'ORD-1001'
        second = graph.invoke({'question': 'When will it arrive?'}, config=config())
        assert 'ORD-1001' in second['resolved_question']
        assert len(second['history']) == 4
    with open_conversation_graph(path, make_toolbox(), model) as graph:
        third = graph.invoke({'question': 'Check that order again'}, config=config())
        assert 'ORD-1001' in third['resolved_question']
        assert len(third['history']) == 6


def test_thread_isolation(tmp_path):
    with open_conversation_graph(tmp_path / 'db.sqlite', make_toolbox(), model) as graph:
        graph.invoke({'question': 'Check ORD-1001'}, config=config('A'))
        other = graph.invoke({'question': 'When will it arrive?'}, config=config('B'))
        assert other.get('last_order_id') is None
        assert 'ORD-1001' not in other['resolved_question']
        assert len(other['history']) == 2


def test_namespace_isolation(tmp_path):
    with open_conversation_graph(tmp_path / 'db.sqlite', make_toolbox(), model) as graph:
        graph.invoke({'question': 'Check ORD-1001'}, config=config('same', 'tenant1', 'u1'))
        other = graph.invoke({'question': 'When will it arrive?'}, config=config('same', 'tenant2', 'u2'))
        assert other.get('last_order_id') is None


def test_no_ticket_creation_or_token_persistence(tmp_path):
    toolbox = make_toolbox()
    with open_conversation_graph(tmp_path / 'db.sqlite', toolbox, model) as graph:
        state = graph.invoke({'question': 'Please create a ticket for ORD-1001'}, config=config())
        assert toolbox.tickets.count() == 0
        assert 'pending_drafts' not in state
        assert 'token' not in str(state).lower()


def test_missing_ids_rejected():
    with pytest.raises(ValueError):
        thread_config('', 'tenant1', 'u1')


def test_empty_question_rejected(tmp_path):
    with open_conversation_graph(tmp_path / 'db.sqlite', make_toolbox(), model) as graph:
        with pytest.raises(ValueError):
            graph.invoke({'question': '  '}, config=config())


def test_history_bounded(tmp_path):
    with open_conversation_graph(tmp_path / 'db.sqlite', make_toolbox(), model) as graph:
        for i in range(9):
            state = graph.invoke({'question': f'Question {i}'}, config=config())
        assert len(state['history']) == 12
        assert state['history'][0]['content'] == 'Question 3'
