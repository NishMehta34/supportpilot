"""Offline Day 16 demonstration: state survives closing/reopening SQLite."""
import json
from pathlib import Path
from app.conversation_memory import open_conversation_graph, thread_config
from app.support_tools import SupportToolbox, UserContext


def fake_model(messages, schemas):
    return {'role': 'assistant', 'content': 'I can help with that order.'}


def main():
    path = Path('artifacts/day16-checkpoints.sqlite')
    path.parent.mkdir(exist_ok=True)
    if path.exists():
        path.unlink()  # Demo only: deterministic fresh run; never delete a real user's DB.
    toolbox = SupportToolbox(UserContext('demo', 'demo-tenant', 'agent'),
                             retrieve_fn=lambda q, tenant, k: [])
    cfg = thread_config('demo-thread', 'demo-tenant', 'demo')
    with open_conversation_graph(path, toolbox, fake_model) as graph:
        a = graph.invoke({'question': 'Where is ORD-1001?'}, config=cfg)
        b = graph.invoke({'question': 'When will it arrive?'}, config=cfg)
    with open_conversation_graph(path, toolbox, fake_model) as graph:
        c = graph.invoke({'question': 'Check that order again'}, config=cfg)
        other = graph.invoke({'question': 'When will it arrive?'},
                             config=thread_config('other-thread', 'demo-tenant', 'demo'))
    assert 'ORD-1001' in b['resolved_question'] and 'ORD-1001' in c['resolved_question']
    assert 'ORD-1001' not in other['resolved_question']
    assert len(c['history']) == 6 and toolbox.tickets.count() == 0
    report = {'thread_id': 'demo-thread', 'turns': 3,
              'after_restart_resolved_question': c['resolved_question'],
              'history_entries': len(c['history']), 'other_thread_isolated': True,
              'tickets_created': toolbox.tickets.count(), 'passed': True}
    Path('artifacts/day16.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    print('DAY 16 PASSED: context survived restart; threads isolated; 0 tickets created')


if __name__ == '__main__':
    main()
