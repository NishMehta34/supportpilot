from app.support_graph import build_support_graph
from app.support_tools import SupportToolbox, UserContext


def make_toolbox():
    return SupportToolbox(UserContext('u1', 'tenant1', 'agent'),
                          retrieve_fn=lambda query, tenant, k: [])


def fake_chat(messages, schemas):
    return {'role': 'assistant', 'content': 'I can help with that.'}


def test_normal_route():
    toolbox = make_toolbox()
    out = build_support_graph(toolbox, fake_chat).invoke({'task': 'Where is my order?'})
    assert out['events'] == ['classify', 'retrieve', 'tool_decision', 'answer']
    assert out['final_answer'] == 'I can help with that.'


def test_escalation_route():
    toolbox = make_toolbox()
    out = build_support_graph(toolbox, fake_chat).invoke({'task': 'I need a human agent'})
    assert out['events'] == ['classify', 'retrieve', 'tool_decision', 'escalate']
    assert 'human' in out['final_answer']
    assert toolbox.tickets.count() == 0


def test_graph_has_no_confirmation_tool():
    toolbox = make_toolbox()
    assert 'confirm' not in [s['function']['name'] for s in toolbox.schemas]
    assert 'error' in toolbox.execute('confirm_ticket', {'draft_id': 'DRAFT-0001'})


def test_retrieval_failure_is_contained():
    toolbox = SupportToolbox(UserContext('u1', 'tenant1', 'agent'),
                             retrieve_fn=lambda *args: 1 / 0)
    out = build_support_graph(toolbox, fake_chat).invoke({'task': 'Return policy?'})
    assert 'unavailable' in out['retrieval']['error'].lower()
    assert out['route'] == 'answer'
