from pathlib import Path
from scripts.day29_portfolio_check import audit

ROOT = Path(__file__).resolve().parents[1]

def test_portfolio_artifacts_present():
    assert audit(ROOT)['checks']['files_present']

def test_diagram_exists():
    assert audit(ROOT)['checks']['architecture_mermaid']

def test_case_study_discloses_limitations():
    assert audit(ROOT)['checks']['case_study_has_limitations']

def test_readme_has_setup():
    assert audit(ROOT)['checks']['readme_has_setup']

def test_readme_has_security():
    assert audit(ROOT)['checks']['readme_has_security']

def test_demo_has_timing():
    assert audit(ROOT)['checks']['demo_script_has_timing']
