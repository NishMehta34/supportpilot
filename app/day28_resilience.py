"""Day 28: dependency-independent resilience primitives for controlled failure drills.

These are opt-in adapters, not automatically wired into live chat or ticket APIs.
"""
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass
from threading import Lock
from time import monotonic
from typing import Callable


class DependencyUnavailable(RuntimeError):
    pass


class DeadlineExceeded(RuntimeError):
    pass


@dataclass(frozen=True)
class Outcome:
    status: str
    value: object = None
    retryable: bool = False


def guarded_call(fn: Callable, *, deadline_s: float = 1.0, fallback=None) -> Outcome:
    """Fail closed on dependency errors and bounded waits.

    The worker thread is NOT cancelled on timeout. Use only for side-effect-free reads.
    """
    if deadline_s <= 0:
        raise ValueError('deadline_s must be positive')
    pool = ThreadPoolExecutor(max_workers=1)
    future = pool.submit(fn)
    try:
        return Outcome('ok', future.result(timeout=deadline_s))
    except FutureTimeout:
        future.cancel()
        return Outcome('timeout', fallback, retryable=True)
    except (DependencyUnavailable, ConnectionError, OSError):
        return Outcome('unavailable', fallback, retryable=True)
    except Exception:
        return Outcome('error', fallback, retryable=False)
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


class ScopedIdempotency:
    """Thread-safe in-process request deduplication; not durable across restarts."""
    def __init__(self):
        self._lock = Lock()
        self._results = {}

    def execute(self, tenant_id: str, user_id: str, key: str, action: Callable):
        if not all(isinstance(x, str) and x.strip() for x in (tenant_id, user_id, key)):
            raise ValueError('tenant, user and idempotency key required')
        if len(key) > 128:
            raise ValueError('idempotency key too long')
        scope = (tenant_id, user_id, key)
        with self._lock:
            if scope in self._results:
                return self._results[scope], True
            # Hold lock while action executes to prevent concurrent duplicates.
            # Failed actions are not cached; callers may retry explicitly.
            result = action()
            self._results[scope] = result
            return result, False


def readiness(*, model_probe: Callable, db_probe: Callable) -> dict:
    """Liveness is distinct from readiness; no raw exception details exposed."""
    checks = {}
    for name, probe in [('model', model_probe), ('database', db_probe)]:
        result = guarded_call(probe, deadline_s=0.25, fallback=False)
        checks[name] = result.status == 'ok' and result.value is True
    return {'ready': all(checks.values()), 'dependencies': checks}


def bounded_retrieval(retrieve: Callable, *, timeout_s: float = 0.25) -> Outcome:
    """A failed retrieval must not be represented as an empty successful search."""
    outcome = guarded_call(retrieve, deadline_s=timeout_s)
    if outcome.status != 'ok':
        return outcome
    if not isinstance(outcome.value, list):
        return Outcome('error')
    return Outcome('empty' if not outcome.value else 'ok', outcome.value)


def restart_state_check(before: dict, after: dict) -> dict:
    """Compare state snapshots for a restart drill; do not imply persistence exists."""
    lost = sorted(set(before) - set(after))
    changed = sorted(k for k in before.keys() & after.keys() if before[k] != after[k])
    return {'passed': not lost and not changed, 'lost': lost, 'changed': changed}
