"""Offline Day 27 adversarial smoke demonstration."""
import json
from pathlib import Path
from app.day27_security import tenant_checked_retrieval
from app.support_tools import SupportToolbox, UserContext, TicketStore

def main():
    store=TicketStore()
    ctx=UserContext('alice','tenant-a','agent')
    def foreign(*_):
        return [{'tenant_id':'tenant-b','doc_id':'secret','section':'private','content':'secret','score':0.99}]
    box=SupportToolbox(ctx,tenant_checked_retrieval(foreign),ticket_store=store)
    report={
        'foreign_tenant_retrieval_blocked': 'error' in box.execute('search_kb',{'query':'private'}),
        'model_cannot_confirm': 'error' in box.execute('confirm_ticket',{'draft_id':'x','token':'y'}),
        'malformed_write_blocked': 'error' in box.execute('create_ticket',{'confirmed':True}),
        'no_ticket_created': store.count()==0,
        'known_open_risks': ['Legacy get_order/get_customer do not enforce tenant ownership',
                             'Strict retrieval adapter must be wired into every real RAG entry point',
                             'Live agent and MCP security need integration tests'],
    }
    path=Path('artifacts/day27_security.json');path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report,indent=2)+'\n')
    assert all(report[k] for k in ('foreign_tenant_retrieval_blocked','model_cannot_confirm','malformed_write_blocked','no_ticket_created'))
    print('DAY 27 SMOKE PASSED: strict retrieval and ticket boundary')
    print('OPEN SECURITY FINDINGS: see docs/day27-threat-model.md')
    print('Report:',path)

if __name__=='__main__':main()
