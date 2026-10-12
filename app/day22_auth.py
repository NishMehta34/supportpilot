"""Local development JWT authentication. Not a production identity provider."""
import os
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ALGORITHM = 'HS256'
ROLES = {'viewer', 'agent', 'admin'}
bearer = HTTPBearer(auto_error=False)

@dataclass(frozen=True)
class Principal:
    user_id: str
    tenant_id: str
    role: str

def signing_key():
    key = os.environ.get('SUPPORTPILOT_JWT_SECRET', '')
    if len(key) < 32:
        raise RuntimeError('SUPPORTPILOT_JWT_SECRET must be at least 32 characters')
    return key

def issue_token(principal: Principal, ttl_minutes=30):
    if principal.role not in ROLES or not principal.user_id or not principal.tenant_id:
        raise ValueError('invalid principal')
    now = datetime.now(timezone.utc)
    return jwt.encode({'sub':principal.user_id, 'tenant_id':principal.tenant_id,
                       'role':principal.role, 'iat':now, 'exp':now+timedelta(minutes=ttl_minutes),
                       'iss':'supportpilot-local', 'aud':'supportpilot-api'}, signing_key(), algorithm=ALGORITHM)

def verify_token(token: str) -> Principal:
    try:
        claims = jwt.decode(token, signing_key(), algorithms=[ALGORITHM],
                            issuer='supportpilot-local', audience='supportpilot-api', options={'require':['sub','tenant_id','role','exp','iat','iss','aud']})
        p = Principal(claims['sub'], claims['tenant_id'], claims['role'])
        if not all(isinstance(x,str) and x.strip() for x in (p.user_id,p.tenant_id,p.role)) or p.role not in ROLES:
            raise ValueError('invalid claims')
        return p
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise HTTPException(status_code=401, detail='invalid_token', headers={'WWW-Authenticate':'Bearer'})

def current_principal(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if credentials is None or credentials.scheme.lower() != 'bearer':
        raise HTTPException(status_code=401, detail='authentication_required', headers={'WWW-Authenticate':'Bearer'})
    return verify_token(credentials.credentials)

def require_agent(principal: Principal):
    if principal.role not in {'agent','admin'}:
        raise HTTPException(status_code=403, detail='insufficient_role')
