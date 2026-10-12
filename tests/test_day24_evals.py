import json
from evals.run import load_cases, fixture_result, evaluate, summarize, gate


def test_thirty_cases():
    assert len(load_cases()) == 30


def test_unique_ids():
    assert len({c["id"] for c in load_cases()}) == 30


def test_fixture_metrics():
    s = summarize(evaluate(load_cases(), fixture_result))
    assert all(s[k] == 1 for k in ("routing_accuracy","retrieval_hit_at_5","citation_rate","tool_success"))


def test_fixture_gate():
    s = summarize(evaluate(load_cases(), fixture_result))
    assert not gate(s, json.loads(__import__('pathlib').Path('evals/day24_baseline.json').read_text()))


def test_routing_regression_caught():
    def broken(c):
        out=fixture_result(c)
        out['route']='wrong'
        return out
    assert any('routing_accuracy' in f for f in gate(summarize(evaluate(load_cases(),broken)),{}))


def test_retrieval_regression_caught():
    def broken(c):
        out=fixture_result(c)
        out['retrieved_doc_ids']=[]
        return out
    assert any('retrieval_hit_at_5' in f for f in gate(summarize(evaluate(load_cases(),broken)),{}))


def test_citation_regression_caught():
    def broken(c):
        out=fixture_result(c)
        out['citations']=[]
        return out
    assert any('citation_rate' in f for f in gate(summarize(evaluate(load_cases(),broken)),{}))


def test_tool_regression_caught():
    def broken(c):
        out=fixture_result(c)
        out['tool_ok']=False
        return out
    assert any('tool_success' in f for f in gate(summarize(evaluate(load_cases(),broken)),{}))


def test_unsupported_fails_gate():
    s=summarize(evaluate(load_cases(),lambda c:{'supported':False}))
    assert any('unsupported' in f for f in gate(s,{}))


def test_errors_fail_closed():
    def broken(c):
        raise RuntimeError('secret in exception')
    entries=evaluate(load_cases(),broken)
    assert all(e['error_type']=='RuntimeError' for e in entries)
    assert 'secret in exception' not in str(entries)


def test_latency_regression():
    s=summarize(evaluate(load_cases(),lambda c:{**fixture_result(c),'latency_ms':100}))
    assert any('latency' in f for f in gate(s,{'latency_ms':{'p95':10}}))
