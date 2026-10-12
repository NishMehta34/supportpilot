"""Application services: API routes should not implement business operations."""
from fastapi import HTTPException
from app.support_tools import PendingActionStore, SupportToolbox, TicketStore, UserContext

class SupportService:
    def __init__(self, repository, chat_handler=None):
        self.repository = repository
        self.chat_handler = chat_handler or self._default_chat
        self.pending = PendingActionStore()
        self.tickets = TicketStore()

    @staticmethod
    def _default_chat(message, tenant_id, user_id, thread_id):
        # No fabricated LLM response: Day 21 defines the API boundary only.
        return {'answer': 'Agent not configured; inject a Day 16 conversation handler.', 'configured': False}

    def chat(self, request):
        if not self.repository.get_thread(request.thread_id, request.tenant_id, request.user_id):
            raise HTTPException(status_code=404, detail='thread_not_found')
        result = self.chat_handler(request.message, request.tenant_id, request.user_id, request.thread_id)
        return {'thread_id': request.thread_id, **result}

    def draft_ticket(self, request):
        # Role is hardcoded for a local demonstration only; NOT authenticated.
        toolbox = SupportToolbox(
            UserContext(user_id=request.user_id, tenant_id=request.tenant_id, role='agent'),
            retrieve_fn=lambda *_: [], pending_store=self.pending, ticket_store=self.tickets)
        result = toolbox.execute('create_ticket', {'customer_id': request.customer_id,
            'subject': request.subject, 'description': request.description})
        if 'error' in result:
            raise HTTPException(status_code=422, detail=result['error'])
        return result
