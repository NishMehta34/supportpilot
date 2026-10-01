"""Day 9: a FastAPI service exposing /ask.

Run it with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.model_adapter import OllamaAdapter
from app.rag import ask_question
from app.retrieval import make_retriever

app = FastAPI(title="SupportPilot RAG API")

_retrieve = make_retriever()
_adapter = OllamaAdapter()


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    tenant_id: str = Field(min_length=1, max_length=100)


class Source(BaseModel):
    source_id: str
    doc_id: str
    section: str
    snippet: str
    score: float | None = None


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    not_found: bool


@app.get("/health")
def health():
    return {"status": "ok"}


def _chat_fn(messages):
    """Adapt OllamaAdapter's chat() (returns a message dict) to the plain-string
    shape app.rag.ask_question expects."""
    return _adapter.chat(messages).get("content", "")


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    result = ask_question(
        question=request.question,
        tenant_id=request.tenant_id,
        retrieve_fn=_retrieve,
        chat_fn=_chat_fn,
    )
    return AskResponse(**{k: result[k] for k in ("answer", "sources", "not_found")})
