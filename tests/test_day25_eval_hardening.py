"""Day 25: regression tests for invalid benchmark timing data."""
import json
import math
import pytest
from evals.run import evaluate, fixture_result, gate, load_cases, summarize


@pytest.mark.parametrize('bad', [-1, float('nan'), float('inf'), -float('inf'), 'not-a-number'])
def test_invalid_latency_fails_closed(bad):
    cases = load_cases()
    def adapter(case):
        return {**fixture_result(case), 'latency_ms': bad}
    entries = evaluate(cases, adapter)
    assert len(entries) == 30
    assert all(e['error_type'] in {'ValueError', 'OverflowError'} for e in entries)
    summary = summarize(entries)
    assert summary['routing_accuracy'] == 0
    assert summary['latency_ms']['p95'] is None
    assert gate(summary, {})
    assert 'NaN' not in json.dumps(entries)


def test_valid_latency_preserved():
    cases = load_cases()
    entries = evaluate(cases, lambda c: {**fixture_result(c), 'latency_ms': 12.5})
    assert all(e['latency_ms'] == 12.5 for e in entries)
    assert summarize(entries)['latency_ms']['p95'] == 12.5
    assert not gate(summarize(entries), {})
