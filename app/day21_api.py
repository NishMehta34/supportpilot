"""Day 21 modular FastAPI service; run: uvicorn app.day21_api:app --reload."""
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from app.day21_models import ChatRequest, DocumentRequest, ThreadRequest, TicketDraftRequest
from app.day21_repositories import InMemoryRepository
from app.day21_services import SupportService


def create_app(service=None):
    api = FastAPI(title='SupportPilot Service API', version='0.21.0',
                  description='Day 21 development API; identity is unverified until Day 22.')
    svc = service or SupportService(InMemoryRepository())
    api.state.service = svc
    def get_service():
        return api.state.service

    health = APIRouter(tags=['health'])
    threads = APIRouter(prefix='/threads', tags=['threads'])
    chat = APIRouter(tags=['chat'])
    documents = APIRouter(prefix='/documents', tags=['documents'])
    tickets = APIRouter(prefix='/tickets', tags=['tickets'])

    @health.get('/health')
    def health_check():
        return {'status': 'ok'}

    @threads.post('', status_code=201)
    def create_thread(body: ThreadRequest, s=Depends(get_service)):
        return s.repository.create_thread(body.tenant_id, body.user_id, body.title)

    @threads.get('')
    def list_threads(tenant_id: str = Query(min_length=1), user_id: str = Query(min_length=1), s=Depends(get_service)):
        return s.repository.list_threads(tenant_id, user_id)

    @threads.get('/{thread_id}')
    def get_thread(thread_id: str, tenant_id: str, user_id: str, s=Depends(get_service)):
        result = s.repository.get_thread(thread_id, tenant_id, user_id)
        if result is None:
            raise HTTPException(status_code=404, detail='thread_not_found')
        return result

    @chat.post('/chat')
    def post_chat(body: ChatRequest, s=Depends(get_service)):
        return s.chat(body)

    @documents.post('', status_code=201)
    def create_document(body: DocumentRequest, s=Depends(get_service)):
        return s.repository.create_document(body.tenant_id, body.user_id, body.title, body.content)

    @documents.get('')
    def list_documents(tenant_id: str = Query(min_length=1), user_id: str = Query(min_length=1), s=Depends(get_service)):
        return s.repository.list_documents(tenant_id, user_id)

    @tickets.post('', status_code=201)
    def create_ticket_draft(body: TicketDraftRequest, s=Depends(get_service)):
        return s.draft_ticket(body)

    @tickets.get('')
    def list_tickets(tenant_id: str = Query(min_length=1), user_id: str = Query(min_length=1), s=Depends(get_service)):
        # No confirmation tokens are exposed by this API.
        return [t for t in s.tickets.all() if t['tenant_id'] == tenant_id and t['created_by'] == user_id]

    for router in (health, threads, chat, documents, tickets):
        api.include_router(router)
    return api

app = create_app()
