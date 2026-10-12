"""Offline Day 17 memory demo: no model, Docker, or network required."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from app.long_term_memory import open_memory_store, invoke_with_memory


class RecordingGraph:
    def invoke(self, state, config):
        return {'resolved_question': state['question'], 'config': config}


def main():
    with TemporaryDirectory() as directory:
        path = Path(directory) / 'memory.sqlite'
        with open_memory_store(path) as memory:
            memory.remember('tenant1', 'u1', 'preferred_language', 'gujarati', consent=True)
            memory.remember('tenant1', 'u1', 'support_tier', 'gold', consent=True)
        with open_memory_store(path) as memory:
            relevant = memory.recall('tenant1', 'u1', 'What language should you speak?')
            unrelated = memory.recall('tenant1', 'u1', 'Where is ORD-1001?')
            isolated = memory.recall('tenant2', 'u1', 'What language should you speak?')
            result = invoke_with_memory(RecordingGraph(), memory, tenant_id='tenant1',
                                        user_id='u1', thread_id='demo',
                                        question='What language should you speak?')
            deleted = memory.forget('tenant1', 'u1', 'preferred_language')
            after_delete = memory.recall('tenant1', 'u1', 'What language should you speak?')
            assert relevant == {'preferred_language': 'gujarati'}
            assert unrelated == isolated == after_delete == {}
            assert deleted == 1 and 'gujarati' in result['resolved_question']
            report = {'restart_persistence': True, 'selective_retrieval': True,
                      'tenant_isolation': True, 'deleted_preference': True,
                      'remaining_tier': memory.recall('tenant1', 'u1', 'support tier'),
                      'passed': True}
    Path('artifacts').mkdir(exist_ok=True)
    Path('artifacts/day17.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    print('DAY 17 PASSED: selective memory, restart, isolation and deletion')


if __name__ == '__main__':
    main()
