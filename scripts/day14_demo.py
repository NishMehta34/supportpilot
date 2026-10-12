import json
from pathlib import Path
from app.support_graph import build_support_graph
from app.support_tools import SupportToolbox, UserContext


def fake_chat(messages, schemas):
    return {'role': 'assistant', 'content': 'Please provide your order ID so I can look it up.'}


def main():
    toolbox = SupportToolbox(UserContext('demo', 'demo-tenant', 'agent'),
                             retrieve_fn=lambda q, t, k: [])
    graph = build_support_graph(toolbox, fake_chat)
    runs = [graph.invoke({'task': prompt}) for prompt in
            ('Where is my order?', 'I need a human agent to review this')]
    assert runs[0]['events'][-1] == 'answer'
    assert runs[1]['events'][-1] == 'escalate'
    assert toolbox.tickets.count() == 0
    output = [{'task': r['task'], 'events': r['events'], 'route': r['route'],
               'final_answer': r['final_answer']} for r in runs]
    path = Path('artifacts/day14.json')
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(output, indent=2))
    print(json.dumps(output, indent=2))
    print('DAY 14 PASSED: normal + escalation routes; 0 tickets created')

if __name__ == '__main__':
    main()
