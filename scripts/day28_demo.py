"""Run with python -m scripts.day28_demo. Writes a truthful drill report."""
import json
from pathlib import Path
from app.day28_resilience import (DependencyUnavailable, ScopedIdempotency,
    guarded_call, readiness, bounded_retrieval, restart_state_check)


def main():
    def down(): raise DependencyUnavailable('offline')
    model = guarded_call(down)
    database = readiness(model_probe=lambda: True, db_probe=lambda: False)
    retrieval = bounded_retrieval(lambda: [])
    store = ScopedIdempotency(); count = [0]
    def draft(): count[0] += 1; return {'draft_id': 'd1'}
    store.execute('tenant-a','alice','req-1',draft)
    _, duplicate = store.execute('tenant-a','alice','req-1',draft)
    restart = restart_state_check({'thread-1': ['hi']}, {})
    report = {
        'kind': 'offline_simulation',
        'model_outage_handled': model.status == 'unavailable',
        'database_outage_detected': database['ready'] is False,
        'empty_retrieval_handled': retrieval.status == 'empty',
        'duplicate_draft_prevented_in_process': duplicate and count[0] == 1,
        'restart_without_persistence_detected': not restart['passed'],
        'live_docker_or_postgres_tested': False,
        'durable_idempotency_tested': False,
        'live_langgraph_recovery_tested': False,
    }
    assert all(report[k] for k in ('model_outage_handled','database_outage_detected',
        'empty_retrieval_handled','duplicate_draft_prevented_in_process',
        'restart_without_persistence_detected'))
    path = Path('artifacts/day28_readiness.json'); path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + '\n')
    print('DAY 28 OFFLINE DRILLS PASSED: simulated outages, empty retrieval, deduplication')
    print('OPEN: live restart recovery, durable idempotency, Docker/PostgreSQL integration')
    print(f'Report: {path}')

if __name__ == '__main__': main()
