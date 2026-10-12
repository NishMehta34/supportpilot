"""Run 10 reproducible, synthetic operations; save redacted traces and report."""
import json
from pathlib import Path
from app.observability import observe_run, troubleshooting_report


def main():
    root = Path('artifacts/day19-traces')
    root.mkdir(parents=True, exist_ok=True)
    # Keep historical evidence: use a unique batch prefix.
    import uuid
    batch = uuid.uuid4().hex[:12]
    for i in range(10):
        def operation(i=i):
            if i in (3, 8):
                raise TimeoutError('simulated tool timeout')
            return {'trace': [{'tool': 'search_kb'}, {'tool': 'get_order'}], 'final_answer': 'synthetic'}
        try:
            observe_run(operation, thread_id=f'demo-{i}', model='scripted',
                        request_id=f'{batch}-{i:02d}', artifact_dir=root)
        except TimeoutError:
            pass
    # Only summarize this batch, avoiding traces from prior demo executions.
    batch_dir = Path('artifacts') / f'day19-batch-{batch}'
    batch_dir.mkdir(parents=True, exist_ok=True)
    for p in root.glob(f'{batch}-*.json'):
        (batch_dir / p.name).write_bytes(p.read_bytes())
    report = troubleshooting_report(batch_dir)
    report['batch_id'] = batch
    Path('artifacts/day19-report.json').write_text(json.dumps(report, indent=2) + '\n')
    assert report['runs'] == 10 and report['failed'] == 2
    print('DAY 19 PASSED: 10 runs, 8 successes, 2 diagnosed failures')
    print('Report: artifacts/day19-report.json')


if __name__ == '__main__':
    main()
