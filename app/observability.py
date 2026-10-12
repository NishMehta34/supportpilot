"""Day 19: safe, structured agent execution diagnostics.

Records metadata and sanitized step summaries, never prompts, responses, tokens,
customer data, or raw tool arguments. Intended for local diagnostics.
"""
import json
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

LOGGER = logging.getLogger('supportpilot.observability')
_ALLOWED = re.compile(r'^[A-Za-z0-9_.:-]{1,128}$')


def _identity(value, name):
    if not isinstance(value, str) or not _ALLOWED.fullmatch(value):
        raise ValueError(f'{name} must be a safe nonempty identifier (max 128 characters)')
    return value


def _summarize_steps(result):
    """Only capture tool name, status, and index, never model text or arguments."""
    if not isinstance(result, dict):
        return []
    trace = result.get('trace', [])
    if not isinstance(trace, list):
        return []
    safe = []
    for index, step in enumerate(trace[:100]):
        if not isinstance(step, dict):
            continue
        tool = step.get('tool') or step.get('tool_name') or 'unknown'
        if not isinstance(tool, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]{0,63}', tool):
            tool = 'unknown'
        status = 'error' if step.get('error') else 'ok'
        safe.append({'step': index + 1, 'tool': tool, 'status': status})
    return safe


def observe_run(operation, *, thread_id, model, request_id=None, artifact_dir=None):
    """Execute a zero-argument operation and record success or failure.

    Errors are re-raised. `operation` is injected for deterministic tests.
    Avoid passing raw exceptions to logs: they can contain sensitive data.
    """
    thread_id = _identity(thread_id, 'thread_id')
    model = _identity(model, 'model')
    request_id = _identity(request_id or uuid.uuid4().hex, 'request_id')
    started = time.perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()
    record = {'request_id': request_id, 'thread_id': thread_id,
              'model': model, 'timestamp': timestamp}
    result = None
    error = None
    try:
        result = operation()
        record['success'] = True
        return result
    except Exception as exc:
        record['success'] = False
        error = type(exc).__name__
        raise
    finally:
        record['latency_ms'] = round((time.perf_counter() - started) * 1000, 3)
        record['error_type'] = error
        record['steps'] = _summarize_steps(result)
        record['tool'] = record['steps'][-1]['tool'] if record['steps'] else None
        record['step_count'] = len(record['steps'])
        LOGGER.info(json.dumps(record, separators=(',', ':')))
        if artifact_dir is not None:
            root = Path(artifact_dir)
            root.mkdir(parents=True, exist_ok=True)
            # Exclusive create: no overwrites, no path traversal from request ID.
            with (root / f'{request_id}.json').open('x', encoding='utf-8') as fh:
                json.dump(record, fh, indent=2)


def load_trace(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def troubleshooting_report(directory):
    """Summarize trace JSON files; do not load unrelated artifacts."""
    records = [load_trace(p) for p in sorted(Path(directory).glob('*.json'))]
    if not records:
        raise ValueError('No trace JSON files found')
    failed = [r for r in records if not r['success']]
    return {'runs': len(records), 'successful': len(records) - len(failed),
            'failed': len(failed),
            'average_latency_ms': round(sum(r['latency_ms'] for r in records) / len(records), 3),
            'failures': [{'request_id': r['request_id'], 'error_type': r['error_type'],
                          'thread_id': r['thread_id']} for r in failed]}
