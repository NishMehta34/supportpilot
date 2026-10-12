"""Offline Day 15 graph demo. No Ollama or database required."""
import json
from pathlib import Path
from app.agentic_rag import build_agentic_rag_graph
from app.support_tools import SupportToolbox, UserContext


def fake_chat(messages, schemas):
    if any(m.get('role')=='tool' for m in messages):
        return {'role':'assistant','content':'I checked the available information.'}
    text=messages[1]['content'].lower()
    if 'ord-1001' in text:
        return {'role':'assistant','content':'','tool_calls':[{'function':{'name':'get_order','arguments':{'order_id':'ORD-1001'}}}]}
    if 'cus-001' in text:
        return {'role':'assistant','content':'','tool_calls':[{'function':{'name':'get_customer','arguments':{'customer_id':'CUS-001'}}}]}
    return {'role':'assistant','content':'Please provide an order or customer ID.'}


def main():
    t=SupportToolbox(UserContext('demo','demo-tenant','agent'), lambda q,tenant,k: [])
    graph=build_agentic_rag_graph(t,fake_chat)
    prompts=['Check order ORD-1001','Find customer CUS-001','What is the warranty policy?',
             'I want a human agent']
    outputs=[]
    for task in prompts:
        out=graph.invoke({'task':task})
        outputs.append({'task':task,'events':out['events'],'route':out['route'],
                        'answer':out['final_answer'],'failure':out.get('failure'),
                        'tool_calls':[x['tool'] for x in out.get('agent_result',{}).get('trace',[])
                                      if x['type']=='tool_call']})
    assert t.tickets.count()==0
    assert outputs[-1]['events'][-1]=='escalate'
    path=Path('artifacts/day15.json')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(outputs,indent=2))
    print(json.dumps(outputs,indent=2))
    print('DAY 15 DEMO PASSED: routing + 0 unauthorized tickets')

if __name__=='__main__':
    main()
