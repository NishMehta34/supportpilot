"""Day 29 portfolio artifact checker. Run: python3 -m scripts.day29_portfolio_check"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    'README-day29.md', 'docs/day29-architecture.md',
    'docs/day29-case-study.md', 'docs/day29-demo-script.md',
    'docs/day29-screenshots.md',
]

def audit(root: Path = ROOT) -> dict:
    missing = [p for p in REQUIRED if not (root / p).is_file()]
    docs = {p: (root / p).read_text(encoding='utf-8') for p in REQUIRED if (root / p).is_file()}
    checks = {
        'files_present': not missing,
        'architecture_mermaid': '```mermaid' in docs.get('docs/day29-architecture.md', ''),
        'case_study_has_limitations': 'Limitations' in docs.get('docs/day29-case-study.md', ''),
        'readme_has_setup': '## Run locally' in docs.get('README-day29.md', ''),
        'readme_has_security': '## Security and limitations' in docs.get('README-day29.md', ''),
        'demo_script_has_timing': '0:00' in docs.get('docs/day29-demo-script.md', ''),
    }
    return {'checks': checks, 'missing': missing, 'pass': all(checks.values())}

if __name__ == '__main__':
    import json
    result = audit()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['pass'] else 1)
