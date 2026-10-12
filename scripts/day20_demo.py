"""Offline failure-injection demo and budget report."""
import json
from pathlib import Path
from app.guardrails import GuardrailConfig, GuardedToolbox
from app.support_tools import SupportToolbox, UserContext


def main():
    toolbox = SupportToolbox(UserContext('demo', 'tenant1', 'agent'), retrieve_fn=lambda q,t,k: [])
    guard = GuardedToolbox(toolbox, GuardrailConfig(max_tool_calls=4))
    results = {
        'unknown_confirmation': guard.execute('confirm_ticket', {'draft_id': 'DRAFT-0001'}),
        'oversized_query': guard.execute('search_kb', {'query': 'x'*3000}),
        'normal_read': guard.execute('get_order', {'order_id': 'ORD-1001'}),
    }
    # Deliberately exceed the call budget. No writes are attempted.
    for _ in range(5):
        results.setdefault('budget_attempts', []).append(guard.execute('search_kb', {'query': 'returns'}))
    results['budget'] = guard.budget_report()
    assert results['unknown_confirmation']['error'] == 'unknown_tool'
    assert results['oversized_query']['error'] == 'arguments_too_large'
    assert results['budget_attempts'][-1]['error'] == 'tool_budget_exhausted'
    assert 'write_once' not in results['budget']['events']
    out = Path('artifacts/day20-budget.json')
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(results, indent=2, default=str))
    print('DAY 20 PASSED: unsafe calls denied; budget enforced; no writes attempted')
    print('Report:', out)


if __name__ == '__main__':
    main()
