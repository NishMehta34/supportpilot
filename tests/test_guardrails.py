import time
from types import SimpleNamespace
import pytest
from app.guardrails import GuardrailConfig, GuardedToolbox, run_guarded_agent


class FakeToolbox:
    schemas = []
    def __init__(self, role='agent', fn=None):
        self.ctx = SimpleNamespace(role=role)
        self.fn = fn or (lambda name, args: {'ok': True})
        self.calls = []
    def execute(self, name, args):
        self.calls.append(name)
        return self.fn(name, args)
    def pending_for_review(self):
        return []


def test_config_rejects_invalid_steps():
    with pytest.raises(ValueError): GuardrailConfig(max_steps=100)


def test_unknown_tool_denied():
    t = FakeToolbox(); g = GuardedToolbox(t)
    assert g.execute('confirm_ticket', {})['error'] == 'unknown_tool'
    assert not t.calls


def test_viewer_cannot_draft():
    t = FakeToolbox(role='viewer'); g = GuardedToolbox(t)
    assert g.execute('create_ticket', {})['error'] == 'permission_denied'
    assert not t.calls


def test_unknown_role_denied():
    t = FakeToolbox(role='hacker'); g = GuardedToolbox(t)
    assert g.execute('get_order', {'order_id': 'ORD-1001'})['error'] == 'permission_denied'


def test_tool_call_budget():
    t = FakeToolbox(); g = GuardedToolbox(t, GuardrailConfig(max_tool_calls=1))
    assert g.execute('get_order', {'order_id': 'ORD-1001'})['ok']
    assert g.execute('get_order', {'order_id': 'ORD-1001'})['error'] == 'tool_budget_exhausted'
    assert len(t.calls) == 1


def test_large_arguments_rejected():
    t = FakeToolbox(); g = GuardedToolbox(t, GuardrailConfig(max_argument_chars=10))
    assert g.execute('search_kb', {'query': 'x'*100})['error'] == 'arguments_too_large'
    assert not t.calls


def test_read_timeout_returns_promptly():
    def slow(n, a):
        time.sleep(.15)
        return {'ok': True}
    t = FakeToolbox(fn=slow)
    g = GuardedToolbox(t, GuardrailConfig(read_timeout_s=.01))
    start = time.monotonic()
    assert g.execute('get_order', {'order_id': 'ORD-1001'})['error'] == 'tool_timeout'
    assert time.monotonic() - start < .12
    assert len(t.calls) == 1  # timeout is NOT retried


def test_transient_read_retried_once():
    t = FakeToolbox(fn=lambda n, a: {'error': 'temporarily_unavailable'} if len(t.calls) == 1 else {'ok': True})
    g = GuardedToolbox(t)
    assert g.execute('get_order', {'order_id': 'ORD-1001'})['ok']
    assert g.budget_report()['retries'] == 1
    assert len(t.calls) == 2


def test_write_not_retried_on_transient_error():
    t = FakeToolbox(fn=lambda n, a: {'error': 'temporarily_unavailable'})
    g = GuardedToolbox(t)
    assert g.execute('create_ticket', {'customer_id': 'CUS-001'})['error'] == 'temporarily_unavailable'
    assert len(t.calls) == 1
    assert g.budget_report()['retries'] == 0


def test_deadline_exhausted_before_call():
    now = [0.0]
    t = FakeToolbox(); g = GuardedToolbox(t, GuardrailConfig(max_elapsed_s=1), clock=lambda: now[0])
    now[0] = 2.0
    assert g.execute('get_order', {'order_id': 'ORD-1001'})['error'] == 'deadline_exceeded'
    assert not t.calls


def test_oversize_prompt_rejected_without_model():
    t = FakeToolbox()
    assert run_guarded_agent('x'*2001, t, chat_fn=lambda *a, **k: None)['error'] == 'invalid_input'
    assert not t.calls
