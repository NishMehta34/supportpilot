"""Day 22 authenticated API; run uvicorn app.day22_api:app --reload."""
import os
import secrets
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.day21_repositories import InMemoryRepository
from app.day21_services import SupportService
from app.day21_models import ThreadRequest, ChatRequest, DocumentRequest, TicketDraftRequest
from app.day22_auth import Principal, current_principal, issue_token, require_agent
from app.support_tools import SupportToolbox, UserContext

class LoginBody(BaseModel):
    username: str
    password: str

class NewThread(BaseModel):
    title: str = Field(default='New conversation', min_length=1, max_length=120)

class NewDocument(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=10000)

class NewChat(BaseModel):
    thread_id: str
    message: str = Field(min_length=1, max_length=2000)

class NewTicket(BaseModel):
    customer_id: str
    subject: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=2000)

def create_app(service=None, users=None):
    api = FastAPI(title='SupportPilot Authenticated API', version='0.22.0')
    api.state.service = service if service is not None else SupportService(InMemoryRepository())
    # Local-only accounts: supply explicit username -> (password, tenant, user, role).
    # Never enable demo credentials on a public network.
    accounts = users if users is not None else {}

    @api.get('/health')
    def health():
        return {'status':'ok'}

    @api.post('/login')
    def login(body: LoginBody):
        record = accounts.get(body.username)
        if record is None or not secrets.compare_digest(body.password, record[0]):
            raise HTTPException(status_code=401, detail='invalid_credentials')
        p = Principal(user_id=record[2], tenant_id=record[1], role=record[3])
        return {'access_token':issue_token(p), 'token_type':'bearer'}

    @api.get('/me')
    def me(p: Principal = Depends(current_principal)):
        return {'user_id':p.user_id,'tenant_id':p.tenant_id,'role':p.role}

    @api.post('/threads', status_code=201)
    def create_thread(body: NewThread, p: Principal = Depends(current_principal)):
        return api.state.service.repository.create_thread(p.tenant_id,p.user_id,body.title)

    @api.get('/threads')
    def list_threads(p: Principal = Depends(current_principal)):
        return api.state.service.repository.list_threads(p.tenant_id,p.user_id)

    @api.get('/threads/{thread_id}')
    def get_thread(thread_id: str,p: Principal = Depends(current_principal)):
        item=api.state.service.repository.get_thread(thread_id,p.tenant_id,p.user_id)
        if item is None: raise HTTPException(status_code=404,detail='thread_not_found')
        return item

    @api.post('/chat')
    def chat(body: NewChat,p: Principal = Depends(current_principal)):
        req=ChatRequest(tenant_id=p.tenant_id,user_id=p.user_id,thread_id=body.thread_id,message=body.message)
        return api.state.service.chat(req)

    @api.post('/documents',status_code=201)
    def add_document(body: NewDocument,p: Principal = Depends(current_principal)):
        require_agent(p)
        return api.state.service.repository.create_document(p.tenant_id,p.user_id,body.title,body.content)

    @api.get('/documents')
    def documents(p: Principal = Depends(current_principal)):
        return api.state.service.repository.list_documents(p.tenant_id,p.user_id)

    @api.post('/tickets',status_code=201)
    def draft_ticket(body: NewTicket,p: Principal = Depends(current_principal)):
        require_agent(p)
        # Construct the toolbox with verified claims, never request-supplied identity.
        toolbox=SupportToolbox(UserContext(user_id=p.user_id,tenant_id=p.tenant_id,role=p.role),
            retrieve_fn=lambda *_:[],pending_store=api.state.service.pending,ticket_store=api.state.service.tickets)
        result=toolbox.execute('create_ticket',body.model_dump())
        if 'error' in result: raise HTTPException(status_code=422,detail=result['error'])
        return result

    @api.get('/tickets')
    def tickets(p: Principal = Depends(current_principal)):
        return [t for t in api.state.service.tickets.all() if t['tenant_id']==p.tenant_id and t['created_by']==p.user_id]

    return api

# No default accounts. Set up local users explicitly in scripts/tests or a trusted bootstrap.
app=create_app()
