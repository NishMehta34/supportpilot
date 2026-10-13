import threading
import time
from concurrent.futures import ThreadPoolExecutor
import pytest
from app.day28_resilience import (DependencyUnavailable, ScopedIdempotency,
    guarded_call, readiness, bounded_retrieval, restart_state_check)


def test_model_unavailable_graceful():
    def down(): raise DependencyUnavailable('secret connection string')
    result = guarded_call(down, fallback='Temporarily unavailable')
    assert result.status == 'unavailable' and result.retryable
    assert 'secret' not in str(result)


def test_database_unavailable_graceful():
    result = guarded_call(lambda: (_ for _ in ()).throw(ConnectionError('password=secret')))
    assert result.status == 'unavailable' and 'secret' not in str(result)


def test_slow_retrieval_timeout():
    result = bounded_retrieval(lambda: time.sleep(.06) or ['late'], timeout_s=.005)
    assert result.status == 'timeout' and result.value is None


def test_empty_retrieval_is_distinct():
    assert bounded_retrieval(lambda: []).status == 'empty'


def test_invalid_retrieval_result():
    assert bounded_retrieval(lambda: None).status == 'error'


def test_readiness_reports_partial_outage():
    assert readiness(model_probe=lambda: True, db_probe=lambda: False) == {
        'ready': False, 'dependencies': {'model': True, 'database': False}}


def test_readiness_all_healthy():
    assert readiness(model_probe=lambda: True, db_probe=lambda: True)['ready']


def test_restart_active_thread_loss_detected():
    report = restart_state_check({'thread-1': ['hello']}, {})
    assert not report['passed'] and report['lost'] == ['thread-1']


def test_restart_restored_thread_passes():
    assert restart_state_check({'t': ['hello']}, {'t': ['hello']})['passed']


def test_duplicate_ticket_request_deduplicated():
    store = ScopedIdempotency(); calls = []
    def create(): calls.append('created'); return {'draft_id': 'd1'}
    assert store.execute('a','alice','req-1',create)[1] is False
    assert store.execute('a','alice','req-1',create)[1] is True
    assert len(calls) == 1


def test_concurrent_requests_deduplicated():
    store = ScopedIdempotency(); count = [0]
    def create():
        time.sleep(.005); count[0] += 1; return 'draft'
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda _: store.execute('a','alice','req-1',create), range(24)))
    assert count[0] == 1 and all(v == 'draft' for v, _ in results)
    assert sum(not duplicate for _, duplicate in results) == 1


def test_idempotency_scoped_by_tenant_and_user():
    store = ScopedIdempotency(); count = [0]
    def create(): count[0] += 1; return count[0]
    assert store.execute('a','alice','k',create)[0] == 1
    assert store.execute('b','alice','k',create)[0] == 2
    assert store.execute('a','bob','k',create)[0] == 3


def test_failed_write_not_cached():
    store = ScopedIdempotency(); calls = [0]
    def flaky():
        calls[0] += 1
        if calls[0] == 1: raise RuntimeError('failure')
        return 'ok'
    with pytest.raises(RuntimeError): store.execute('a','alice','k',flaky)
    assert store.execute('a','alice','k',flaky) == ('ok', False)


def test_invalid_key_rejected():
    with pytest.raises(ValueError): ScopedIdempotency().execute('a','alice','',lambda: None)


def test_bad_timeout_rejected():
    with pytest.raises(ValueError): guarded_call(lambda: None, deadline_s=0)
