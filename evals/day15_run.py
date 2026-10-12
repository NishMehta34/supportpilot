"""Deterministic 20-case route benchmark; optional real-model runs come later."""
import json
import re
import time
from pathlib import Path
from app.agentic_rag import build_agentic_rag_graph
from app.support_tools import SupportToolbox, UserContext


def scripted_chat(messages, schemas):
    if any(m.get('role')=='tool' for m in messages):
        return {'role':'assistant','content':'I checked the available tool result.'}
    task=messages[1]['content']
    order=re.search(r'ORD-\d+',task,re.I)
    customer=re.search(r'CUS-\d+',task,re.I)
    if 'ticket' in task.lower() and customer:
        name='create_ticket'
        args={'customer_id':customer.group().upper(),'subject':'Support request',
              'description':'Customer requested support for a damaged or broken product.'}
    elif order:
        name,args='get_order',{'order_id':order.group().upper()}
    elif customer:
        name,args='get_customer',{'customer_id':customer.group().upper()}
    else:
        name,args='search_kb',{'query':task}
    return {'role':'assistant','content':'','tool_calls':[{'function':{'name':name,'arguments':args}}]}


def main():
    cases=[json.loads(x) for x in Path('evals/day15_cases.jsonl').read_text().splitlines() if x.strip()]
    assert len(cases)==20
    results=[]
    for case in cases:
        toolbox=SupportToolbox(UserContext('eval','tenant-eval','agent'),lambda q,t,k: [])
        graph=build_agentic_rag_graph(toolbox,scripted_chat)
        start=time.perf_counter()
        out=graph.invoke({'task':case['task']})
        tools=[t['tool'] for t in out.get('agent_result',{}).get('trace',[]) if t['type']=='tool_call']
        route_ok=out['route']==case['expected_route']
        tool_ok=case['expected_tool'] is None or case['expected_tool'] in tools
        safety_ok=toolbox.tickets.count()==0
        passed=route_ok and tool_ok and safety_ok
        results.append({'id':case['id'],'passed':passed,'route':out['route'],
                        'expected_route':case['expected_route'],'tools':tools,
                        'expected_tool':case['expected_tool'],
                        'latency_ms':round((time.perf_counter()-start)*1000,2),
                        'failure':out.get('failure')})
    passed=sum(x['passed'] for x in results)
    report={'benchmark':'day15 scripted routing (not model-quality evaluation)',
            'passed':passed,'total':len(results),'routing_accuracy':round(passed/len(results),3),
            'results':results,'failures':[x for x in results if not x['passed']]}
    path=Path('artifacts/day15-benchmark.json')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,indent=2))
    print(f'DAY 15 BENCHMARK: {passed}/20 passed')
    print(f'Report: {path}')
    if passed<16:
        raise SystemExit('FAIL: below 16/20 acceptance threshold')

if __name__=='__main__':
    main()
