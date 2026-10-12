"""Day 21 API contracts; these are not authentication credentials."""
from pydantic import BaseModel, Field

class Scope(BaseModel):
    tenant_id: str = Field(min_length=1, max_length=100)
    user_id: str = Field(min_length=1, max_length=100)

class ChatRequest(Scope):
    thread_id: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=2000)

class ThreadRequest(Scope):
    title: str = Field(default='New conversation', min_length=1, max_length=120)

class DocumentRequest(Scope):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=10000)

class TicketDraftRequest(Scope):
    customer_id: str = Field(min_length=1, max_length=100)
    subject: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=2000)
