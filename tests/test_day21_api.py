from fastapi.testclient import TestClient
from app.day21_api import create_app
from app.day21_repositories import InMemoryRepository
from app.day21_services import SupportService


def client(chat_handler=None):
    return TestClient(create_app(SupportService(InMemoryRepository(), chat_handler=chat_handler)))


def scope(**kwargs):
    return {'tenant_id': 't1', 'user_id': 'u1', **kwargs}


def test_health():
    assert client().get('/health').json() == {'status': 'ok'}


def test_openapi_routes():
    paths = client().get('/openapi.json').json()['paths']
    assert {'/health', '/chat', '/threads', '/threads/{thread_id}', '/documents', '/tickets'} <= set(paths)


def test_thread_crud_scoped():
    c = client()
    thread = c.post('/threads', json=scope(title='Help')).json()
    assert c.get('/threads', params=scope()).json()[0]['thread_id'] == thread['thread_id']
    assert c.get('/threads/' + thread['thread_id'], params=scope(user_id='u2')).status_code == 404


def test_chat_requires_existing_thread():
    c = client()
    assert c.post('/chat', json=scope(thread_id='missing', message='Hello')).status_code == 404


def test_chat_dependency_injection():
    c = client(lambda msg, tenant, user, thread: {'answer': msg.upper(), 'configured': True})
    thread = c.post('/threads', json=scope()).json()['thread_id']
    result = c.post('/chat', json=scope(thread_id=thread, message='hi')).json()
    assert result['answer'] == 'HI' and result['configured']


def test_default_chat_does_not_fabricate_answer():
    c = client()
    thread = c.post('/threads', json=scope()).json()['thread_id']
    assert c.post('/chat', json=scope(thread_id=thread, message='hi')).json()['configured'] is False


def test_document_metadata_and_scope():
    c = client()
    r = c.post('/documents', json=scope(title='Shipping', content='Secret content')).json()
    assert r['title'] == 'Shipping' and 'content' not in r
    assert len(c.get('/documents', params=scope()).json()) == 1
    assert c.get('/documents', params=scope(tenant_id='t2')).json() == []


def test_document_validation():
    assert client().post('/documents', json=scope(title='X', content='')).status_code == 422


def test_ticket_draft_no_confirmation_token():
    c = client()
    response = c.post('/tickets', json=scope(customer_id='CUS-001', subject='Issue', description='Need help'))
    assert response.status_code == 201, response.text
    assert response.json()['status'] == 'pending_confirmation'
    assert 'token' not in str(response.json())
    assert c.get('/tickets', params=scope()).json() == []


def test_no_ticket_confirmation_endpoint():
    c = client()
    assert c.post('/tickets/confirm', json={}).status_code == 404


def test_invalid_ticket_rejected():
    c = client()
    assert c.post('/tickets', json=scope(customer_id='CUS-001', subject='', description='Issue')).status_code == 422


def test_openapi_docs():
    assert client().get('/docs').status_code == 200
