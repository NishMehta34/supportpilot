"""Offline JWT authentication demo."""
import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.day22_api import create_app

def main():
    import os
    if len(os.environ.get('SUPPORTPILOT_JWT_SECRET',''))<32:
        raise SystemExit('Set SUPPORTPILOT_JWT_SECRET to a random value of at least 32 characters')
    c=TestClient(create_app(users={'alice':('demo-a','tenant-a','alice','agent'),
                                   'bob':('demo-b','tenant-b','bob','viewer')}))
    def headers(name,password):
        r=c.post('/login',json={'username':name,'password':password}); assert r.status_code==200
        return {'Authorization':'Bearer '+r.json()['access_token']}
    a=headers('alice','demo-a'); b=headers('bob','demo-b')
    t=c.post('/threads',headers=a,json={'title':'private'}).json()['thread_id']
    results={'missing_token_rejected':c.get('/threads').status_code==401,
             'cross_tenant_thread_denied':c.get('/threads/'+t,headers=b).status_code==404,
             'cross_tenant_chat_denied':c.post('/chat',headers=b,json={'thread_id':t,'message':'hi'}).status_code==404,
             'viewer_write_denied':c.post('/tickets',headers=b,json={'customer_id':'CUS-1','subject':'Hi','description':'Help'}).status_code==403,
             'valid_user_thread_access':c.get('/threads/'+t,headers=a).status_code==200}
    results['passed']=all(results.values())
    out=Path('artifacts/day22.json');out.parent.mkdir(exist_ok=True,parents=True)
    out.write_text(json.dumps(results,indent=2)+'\n')
    print('DAY 22 PASSED: JWT auth, cross-tenant denial, role enforcement' if results['passed'] else 'DAY 22 FAILED')
    print('Report:',out)
    assert results['passed']
if __name__=='__main__':main()
