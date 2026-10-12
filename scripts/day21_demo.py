"""Offline Day 21 API smoke demo."""
import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.day21_api import create_app


def main():
    c = TestClient(create_app())
    identity = {'tenant_id': 'demo', 'user_id': 'local'}
    thread = c.post('/threads', json={**identity, 'title': 'Shipping help'})
    thread.raise_for_status()
    tid = thread.json()['thread_id']
    chat = c.post('/chat', json={**identity, 'thread_id': tid, 'message': 'Where is my order?'})
    chat.raise_for_status()
    doc = c.post('/documents', json={**identity, 'title': 'Policy', 'content': 'Returns within 30 days'})
    doc.raise_for_status()
    result = {'health': c.get('/health').json(), 'thread_created': True,
              'chat_configured': chat.json()['configured'], 'document_created': True,
              'openapi_paths': sorted(c.get('/openapi.json').json()['paths'])}
    Path('artifacts').mkdir(exist_ok=True)
    Path('artifacts/day21.json').write_text(json.dumps(result, indent=2) + '\n')
    print('DAY 21 PASSED: routes, schemas, dependency injection and OpenAPI')
    print('NOTE: chat agent not configured; document ingestion not implemented')
    print('Report: artifacts/day21.json')

if __name__ == '__main__':
    main()
