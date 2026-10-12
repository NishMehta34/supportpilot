import time
import pytest
from app.agentic_rag import build_agentic_rag_graph
from app.support_tools import SupportToolbox, UserContext


def toolbox(retrieve=None, role='agent'):
    return SupportToolbox(UserContext('u1', 'tenant1', role),
                          retrieve_fn=retrieve or (lambda q,t,k: []))


def response(text='I can help.'):
    return lambda messages, schemas: {'role':'assistant', 'content':text}


def test_normal_route():
    out = build_agentic_rag_graph(toolbox(), response()).invoke({'task':'Where is my order?'})
    assert out['events'] == ['classify','retrieve','tool_decision','answer']
    assert out['final_answer'] == 'I can help.'


def test_escalation_no_model():
    def fail(*args):
        raise AssertionError('model should not be called')
    t = toolbox()
    out = build_agentic_rag_graph(t, fail).invoke({'task':'I want a human agent'})
    assert out['events'][-1] == 'escalate'
    assert t.tickets.count() == 0


def test_search_kb_uses_context_tenant():
    seen=[]
    def retrieve(q,tenant,k):
        seen.append((tenant,k))
        return []
    build_agentic_rag_graph(toolbox(retrieve), response()).invoke({'task':'Warranty policy?'})
    assert seen and all(x[0]=='tenant1' for x in seen)


def test_broken_retrieval_fallback():
    def fail(*args):
        raise RuntimeError('db offline')
    out = build_agentic_rag_graph(toolbox(fail), response()).invoke({'task':'Warranty policy?'})
    assert 'error' in out['retrieval']
    assert out['final_answer'] == 'I can help.'


def test_model_exception_fallback():
    def fail(*args):
        raise RuntimeError('model offline')
    out = build_agentic_rag_graph(toolbox(), fail).invoke({'task':'Warranty policy?'})
    assert out['failure']=='agent_error'
    assert 'unavailable' in out['final_answer']


def test_step_limit_fallback():
    def call(messages,schemas):
        return {'role':'assistant','content':'','tool_calls':[{'function':{'name':'get_order','arguments':{'order_id':'ORD-1001'}}}]}
    out = build_agentic_rag_graph(toolbox(), call, max_steps=1).invoke({'task':'Find order'})
    assert out['failure']=='max_steps_reached'
    assert 'could not safely' in out['final_answer']


def test_model_cannot_confirm():
    t=toolbox()
    def call(messages,schemas):
        if any(m.get('role')=='tool' for m in messages):
            return {'role':'assistant','content':'Ticket created!'}
        return {'role':'assistant','content':'','tool_calls':[{'function':{'name':'confirm_ticket','arguments':{'draft_id':'DRAFT-0001','token':'123'}}}]}
    out=build_agentic_rag_graph(t,call).invoke({'task':'Confirm my ticket'})
    assert t.tickets.count()==0
    assert 'error' in out['agent_result']['trace'][0]['result']


def test_ticket_draft_not_creation():
    t=toolbox()
    def call(messages,schemas):
        if any(m.get('role')=='tool' for m in messages):
            return {'role':'assistant','content':'Ticket created!'}
        return {'role':'assistant','content':'','tool_calls':[{'function':{'name':'create_ticket','arguments':{'customer_id':'CUS-001','subject':'Broken device','description':'Screen cracked'}}}]}
    out=build_agentic_rag_graph(t,call).invoke({'task':'Create a ticket for CUS-001 damaged device'})
    assert t.tickets.count()==0
    if out['pending_drafts']:
        assert 'No ticket has been created' in out['final_answer']
        assert 'token' not in str(out)


def test_invalid_limits():
    with pytest.raises(ValueError):
        build_agentic_rag_graph(toolbox(),max_steps=7)
    with pytest.raises(ValueError):
        build_agentic_rag_graph(toolbox(),tool_timeout_s=0)


def test_agent_timeout_fallback():
    def slow(messages,schemas):
        time.sleep(.06)
        return {'role':'assistant','content':'late'}
    out=build_agentic_rag_graph(toolbox(),slow,agent_timeout_s=.005).invoke({'task':'Status?'})
    assert out['failure']=='agent_timeout'
