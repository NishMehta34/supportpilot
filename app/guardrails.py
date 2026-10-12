"""Day 20: bounded, fail-closed tool boundary for SupportPilot.

Read timeouts stop waiting but cannot kill a running Python thread. Never
execute a write in a background timeout thread; never retry writes.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass
import time

from app.support_tools import READ_ONLY_TOOLS, WRITE_TOOLS, WRITE_ROLES, KNOWN_ROLES


@dataclass(frozen=True)
class GuardrailConfig:
    max_steps: int = 6
    max_tool_calls: int = 8
    max_input_chars: int = 2000
    max_argument_chars: int = 2500
    max_elapsed_s: float = 30.0
    read_timeout_s: float = 2.0
    max_read_attempts: int = 2

    def __post_init__(self):
        if not 1 <= self.max_steps <= 6 or self.max_tool_calls < 1:
            raise ValueError('Invalid step or tool-call budget')
        if self.max_input_chars < 1 or self.max_argument_chars < 1:
            raise ValueError('Invalid input limits')
        if self.max_elapsed_s <= 0 or self.read_timeout_s <= 0:
            raise ValueError('Timeouts must be positive')
        if not 1 <= self.max_read_attempts <= 3:
            raise ValueError('Read attempts must be between 1 and 3')


class GuardedToolbox:
    """Wrap an existing toolbox; preserve its authorization and confirmation rules.

    One wrapper instance is one request. Do not reuse across users or requests.
    """
    def __init__(self, toolbox, config=None, *, clock=time.monotonic):
        self._toolbox = toolbox
        self.config = config or GuardrailConfig()
        self.clock = clock
        self.started = clock()
        self.calls = 0
        self.attempts = 0
        self.timeouts = 0
        self.retries = 0
        self.denied = 0
        self.events = []

    @property
    def schemas(self):
        return self._toolbox.schemas

    def pending_for_review(self):
        return self._toolbox.pending_for_review()

    def budget_report(self):
        return {
            'tool_calls': self.calls, 'attempts': self.attempts,
            'retries': self.retries, 'timeouts': self.timeouts,
            'denied': self.denied, 'elapsed_ms': round((self.clock()-self.started)*1000, 2),
            'events': list(self.events),
        }

    def _reject(self, code):
        self.denied += 1
        self.events.append(code)
        return {'error': code}

    def execute(self, name, arguments):
        if name not in READ_ONLY_TOOLS + WRITE_TOOLS:
            return self._reject('unknown_tool')
        if not isinstance(arguments, dict):
            return self._reject('invalid_arguments')
        if not all(isinstance(k, str) and isinstance(v, (str, int, float, bool, type(None)))
                   for k, v in arguments.items()):
            return self._reject('invalid_arguments')
        if sum(len(k) + len(str(v)) for k, v in arguments.items()) > self.config.max_argument_chars:
            return self._reject('arguments_too_large')
        ctx = self._toolbox.ctx
        if ctx.role not in KNOWN_ROLES or (name in WRITE_TOOLS and ctx.role not in WRITE_ROLES):
            return self._reject('permission_denied')
        if self.calls >= self.config.max_tool_calls:
            return self._reject('tool_budget_exhausted')
        if self.clock() - self.started >= self.config.max_elapsed_s:
            return self._reject('deadline_exceeded')
        self.calls += 1
        # Write actions are synchronous and never retried. The Day 13 toolbox
        # stages drafts only; confirmation is not an exposed tool.
        if name in WRITE_TOOLS:
            self.attempts += 1
            self.events.append('write_once')
            try:
                return self._toolbox.execute(name, arguments)
            except Exception:
                return {'error': 'tool_failed'}
        for attempt in range(self.config.max_read_attempts):
            remaining = self.config.max_elapsed_s - (self.clock() - self.started)
            if remaining <= 0:
                return self._reject('deadline_exceeded')
            self.attempts += 1
            pool = ThreadPoolExecutor(max_workers=1)
            future = pool.submit(self._toolbox.execute, name, arguments)
            try:
                result = future.result(timeout=min(remaining, self.config.read_timeout_s))
            except FutureTimeout:
                self.timeouts += 1
                self.events.append('read_timeout')
                # Timed-out work may still run: do not retry it.
                return {'error': 'tool_timeout'}
            except Exception:
                result = {'error': 'tool_failed'}
            finally:
                pool.shutdown(wait=False, cancel_futures=True)
            # Only explicit, allowlisted transient failures can be retried.
            if (isinstance(result, dict) and result.get('error') == 'temporarily_unavailable'
                    and attempt + 1 < self.config.max_read_attempts):
                self.retries += 1
                self.events.append('retry_read')
                continue
            return result
        return {'error': 'tool_failed'}


def run_guarded_agent(task, toolbox, *, chat_fn, config=None):
    """Run existing Day 13 support agent with bounded tool access."""
    from app.support_agent import run_support_agent
    config = config or GuardrailConfig()
    if not isinstance(task, str) or not task.strip() or len(task) > config.max_input_chars:
        return {'error': 'invalid_input', 'budget': None}
    guard = GuardedToolbox(toolbox, config)
    result = run_support_agent(task, guard, chat_fn=chat_fn, max_steps=config.max_steps)
    result['budget'] = guard.budget_report()
    return result
