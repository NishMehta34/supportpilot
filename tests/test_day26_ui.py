import pytest
from fastapi.testclient import TestClient
from app.day26_api import create_app, local_users_from_environment

@pytest.fixture(autouse=True)
def secret(monkeypatch):
    monkeypatch.setenv('SUPPORTPILOT_JWT_SECRET','local-only-test-secret-at-least-32-characters')

@pytest.fixture
def client():
    return TestClient(create_app(users={
        'alice':('alice-long-test-password','tenant-a','alice','agent'),
        'bob':('bob-long-test-password','tenant-b','bob','agent'),
        'eve':('eve-long-test-password','tenant-a','eve','viewer'),
    }))

def auth(client, user):
    token=client.post('/login',json={'username':user,'password':user+'-long-test-password'}).json()['access_token']
    return {'Authorization':'Bearer '+token}

def draft(client, headers):
    return client.post('/tickets',headers=headers,json={'customer_id':'CUS-001','subject':'Delivery problem','description':'Need help'}).json()

def test_ui_is_served_with_security_headers(client):
    r=client.get('/');assert r.status_code==200 and 'SupportPilot' in r.text
    assert "script-src 'self'" in r.headers['content-security-policy']
    assert 'no-store' in r.headers['cache-control']

def test_script_served(client):
    r=client.get('/day26.js');assert r.status_code==200 and 'javascript' in r.headers['content-type']
    assert 'innerHTML' not in r.text

def test_no_demo_account_by_default(monkeypatch):
    monkeypatch.delenv('SUPPORTPILOT_DAY26_LOCAL_DEMO',raising=False)
    assert local_users_from_environment() is None

def test_demo_requires_password(monkeypatch):
    monkeypatch.setenv('SUPPORTPILOT_DAY26_LOCAL_DEMO','1')
    monkeypatch.delenv('SUPPORTPILOT_DAY26_DEMO_PASSWORD',raising=False)
    with pytest.raises(RuntimeError):local_users_from_environment()

def test_demo_rejected_in_production(monkeypatch):
    monkeypatch.setenv('SUPPORTPILOT_DAY26_LOCAL_DEMO','1')
    monkeypatch.setenv('SUPPORTPILOT_ENV','production')
    monkeypatch.setenv('SUPPORTPILOT_DAY26_DEMO_PASSWORD','a-long-password-here')
    with pytest.raises(RuntimeError):local_users_from_environment()

def test_drafts_require_login(client):
    assert client.get('/ticket-drafts').status_code==401

def test_viewer_cannot_see_drafts(client):
    assert client.get('/ticket-drafts',headers=auth(client,'eve')).status_code==403

def test_human_confirmation_workflow(client):
    a=auth(client,'alice');d=draft(client,a)
    assert d['status']=='pending_confirmation'
    assert client.get('/tickets',headers=a).json()==[]
    items=client.get('/ticket-drafts',headers=a).json()
    assert len(items)==1 and items[0]['draft_id']==d['draft_id']
    result=client.post('/ticket-drafts/'+d['draft_id']+'/confirm',headers=a,json={'token':items[0]['token']})
    assert result.status_code==200 and result.json()['ok']
    assert len(client.get('/tickets',headers=a).json())==1
    assert client.get('/ticket-drafts',headers=a).json()==[]

def test_wrong_token_rejected(client):
    a=auth(client,'alice');d=draft(client,a)
    r=client.post('/ticket-drafts/'+d['draft_id']+'/confirm',headers=a,json={'token':'wrong'})
    assert r.status_code==409 and client.get('/tickets',headers=a).json()==[]

def test_cross_tenant_cannot_confirm(client):
    a,b=auth(client,'alice'),auth(client,'bob');d=draft(client,a)
    token=client.get('/ticket-drafts',headers=a).json()[0]['token']
    assert client.get('/ticket-drafts',headers=b).json()==[]
    assert client.post('/ticket-drafts/'+d['draft_id']+'/confirm',headers=b,json={'token':token}).status_code==404
    assert client.get('/tickets',headers=b).json()==[]

def test_confirm_is_single_use(client):
    a=auth(client,'alice');d=draft(client,a)
    token=client.get('/ticket-drafts',headers=a).json()[0]['token']
    path='/ticket-drafts/'+d['draft_id']+'/confirm'
    assert client.post(path,headers=a,json={'token':token}).status_code==200
    assert client.post(path,headers=a,json={'token':token}).status_code==409
    assert len(client.get('/tickets',headers=a).json())==1

def test_agent_tool_schema_cannot_confirm(client):
    from app.support_tools import SupportToolbox, UserContext
    toolbox=SupportToolbox(UserContext('alice','tenant-a','agent'),retrieve_fn=lambda *_:[])
    assert 'error' in toolbox.execute('confirm_ticket',{'draft_id':'X','token':'Y'})
