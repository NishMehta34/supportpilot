"""Day 26 local browser UI on top of Day 22. Run: uvicorn app.day26_api:app --reload."""
import os
from pathlib import Path
from fastapi import Depends, HTTPException
from fastapi.responses import HTMLResponse
from app.day22_api import create_app as create_auth_app
from app.day22_auth import Principal, current_principal, require_agent
from app.support_tools import SupportToolbox, UserContext

UI_PATH = Path(__file__).with_name('day26_ui.html')

def create_app(service=None, users=None):
    api = create_auth_app(service=service, users=users)
    api.title = 'SupportPilot Browser UI'

    @api.get('/', response_class=HTMLResponse, include_in_schema=False)
    def index():
        return HTMLResponse(UI_PATH.read_text(encoding='utf-8'), headers={
            'Cache-Control': 'no-store',
            'Content-Security-Policy': "default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
            'X-Content-Type-Options': 'nosniff',
            'Referrer-Policy': 'no-referrer',
        })

    @api.get('/day26.js', include_in_schema=False)
    def javascript():
        from fastapi.responses import Response
        return Response(UI_PATH.with_suffix('.js').read_text(encoding='utf-8'), media_type='application/javascript', headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

    def toolbox(p):
        return SupportToolbox(UserContext(user_id=p.user_id, tenant_id=p.tenant_id, role=p.role),
                              retrieve_fn=lambda *_: [], pending_store=api.state.service.pending,
                              ticket_store=api.state.service.tickets)

    @api.get('/ticket-drafts')
    def list_drafts(p: Principal = Depends(current_principal)):
        require_agent(p)
        return toolbox(p).pending_for_review()

    from pydantic import BaseModel, Field
    class ConfirmRequest(BaseModel):
        token: str = Field(min_length=1, max_length=128)

    @api.post('/ticket-drafts/{draft_id}/confirm')
    def confirm_draft(draft_id: str, body: ConfirmRequest, p: Principal = Depends(current_principal)):
        require_agent(p)
        result = toolbox(p).confirm(draft_id, body.token)
        if not result['ok']:
            raise HTTPException(status_code=404 if result['error']=='not_found' else 409, detail=result['error'])
        return result

    return api


def local_users_from_environment():
    """Explicit opt-in local demo; never ship these credentials to production."""
    if os.environ.get('SUPPORTPILOT_DAY26_LOCAL_DEMO') != '1':
        return None
    if os.environ.get('SUPPORTPILOT_ENV', '').lower() in {'production','prod'}:
        raise RuntimeError('Local demo accounts are forbidden in production')
    password = os.environ.get('SUPPORTPILOT_DAY26_DEMO_PASSWORD', '')
    if len(password) < 12:
        raise RuntimeError('Set SUPPORTPILOT_DAY26_DEMO_PASSWORD to at least 12 characters')
    return {'demo-agent': (password, 'local-demo-tenant', 'local-demo-agent', 'agent')}

app = create_app(users=local_users_from_environment())
