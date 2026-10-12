"""Offline end-to-end browser API workflow smoke test."""
import os
from fastapi.testclient import TestClient
from app.day26_api import create_app

def main():
    os.environ.setdefault('SUPPORTPILOT_JWT_SECRET','local-only-demo-secret-at-least-32-characters')
    with TestClient(create_app(users={'demo':('demo-test-password','tenant-a','demo','agent')})) as c:
        assert c.get('/').status_code==200
        token=c.post('/login',json={'username':'demo','password':'demo-test-password'}).json()['access_token']
        h={'Authorization':'Bearer '+token}
        thread=c.post('/threads',headers=h,json={'title':'Delivery help'}).json()
        response=c.post('/chat',headers=h,json={'thread_id':thread['thread_id'],'message':'Where is my order?'}).json()
        assert response['configured'] is False
        draft=c.post('/tickets',headers=h,json={'customer_id':'CUS-001','subject':'Late order','description':'Please help'}).json()
        assert draft['status']=='pending_confirmation' and c.get('/tickets',headers=h).json()==[]
        token=c.get('/ticket-drafts',headers=h).json()[0]['token']
        confirmed=c.post(f"/ticket-drafts/{draft['draft_id']}/confirm",headers=h,json={'token':token}).json()
        assert confirmed['ok'] and len(c.get('/tickets',headers=h).json())==1
        print('DAY 26 PASSED: login, thread, chat boundary, draft, explicit human confirmation')
        print('NOTE: real agent response/citations/streaming and durable persistence are not wired.')
if __name__=='__main__':main()
