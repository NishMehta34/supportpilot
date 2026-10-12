import os
import pytest
from fastapi.testclient import TestClient
from app.day22_api import create_app
from app.day22_auth import Principal, issue_token, verify_token

@pytest.fixture(autouse=True)
def secret(monkeypatch):
    monkeypatch.setenv('SUPPORTPILOT_JWT_SECRET','local-only-test-secret-at-least-32-characters')

@pytest.fixture
def client():
    users={'alice':('alice-test-password','tenant-a','alice','agent'),
           'bob':('bob-test-password','tenant-b','bob','agent'),
           'eve':('eve-test-password','tenant-a','eve','viewer')}
    return TestClient(create_app(users=users))

def auth(client,name):
    token=client.post('/login',json={'username':name,'password':name+'-test-password'}).json()['access_token']
    return {'Authorization':'Bearer '+token}

def test_health_public(client): assert client.get('/health').status_code==200
def test_missing_auth(client): assert client.get('/threads').status_code==401
def test_login_invalid(client): assert client.post('/login',json={'username':'alice','password':'bad'}).status_code==401
def test_login_and_me(client):
    h=auth(client,'alice'); assert client.get('/me',headers=h).json()=={'user_id':'alice','tenant_id':'tenant-a','role':'agent'}
def test_tampered_token(client):
    h=auth(client,'alice'); h['Authorization']+='bad'; assert client.get('/me',headers=h).status_code==401
def test_expired_token(client):
    t=issue_token(Principal('alice','tenant-a','agent'),ttl_minutes=-1)
    assert client.get('/me',headers={'Authorization':'Bearer '+t}).status_code==401
def test_thread_cross_tenant(client):
    a,b=auth(client,'alice'),auth(client,'bob')
    thread=client.post('/threads',headers=a,json={'title':'private'}).json()['thread_id']
    assert client.get('/threads/'+thread,headers=b).status_code==404
    assert client.get('/threads',headers=b).json()==[]
    assert client.post('/chat',headers=b,json={'thread_id':thread,'message':'hello'}).status_code==404
def test_same_tenant_cross_user(client):
    a,e=auth(client,'alice'),auth(client,'eve')
    tid=client.post('/threads',headers=a,json={'title':'private'}).json()['thread_id']
    assert client.get('/threads/'+tid,headers=e).status_code==404
def test_documents_isolation(client):
    a,b=auth(client,'alice'),auth(client,'bob')
    assert client.post('/documents',headers=a,json={'title':'secret','content':'private'}).status_code==201
    assert client.get('/documents',headers=b).json()==[]
def test_viewer_cannot_write(client):
    e=auth(client,'eve')
    assert client.post('/documents',headers=e,json={'title':'x','content':'y'}).status_code==403
    assert client.post('/tickets',headers=e,json={'customer_id':'C','subject':'x','description':'y'}).status_code==403
def test_ticket_draft_no_confirmation(client):
    a=auth(client,'alice')
    r=client.post('/tickets',headers=a,json={'customer_id':'CUS-001','subject':'Help','description':'Need help'})
    assert r.status_code==201
    assert r.json().get('status')=='pending_confirmation'
    assert client.get('/tickets',headers=a).json()==[]
    assert '/tickets/confirm' not in client.get('/openapi.json').json()['paths']
def test_body_identity_ignored(client):
    a=auth(client,'alice')
    r=client.post('/threads',headers=a,json={'title':'hello','tenant_id':'tenant-b','user_id':'bob'})
    assert r.status_code==201
    assert r.json()['tenant_id']=='tenant-a' and r.json()['user_id']=='alice'
def test_missing_secret(monkeypatch):
    monkeypatch.delenv('SUPPORTPILOT_JWT_SECRET')
    with pytest.raises(RuntimeError): issue_token(Principal('a','b','agent'))
def test_invalid_role_token():
    with pytest.raises(ValueError): issue_token(Principal('a','b','superuser'))
