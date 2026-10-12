"""Static deployment checks; no Docker daemon needed."""
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]

def content(name):
    return (ROOT / name).read_text()

def test_services_defined():
    data = content('docker-compose.day23.yml')
    for name in ('  api:', '  db:', '  ollama:'):
        assert name in data

def test_api_waits_for_healthy_dependencies():
    data = content('docker-compose.day23.yml')
    assert data.count('condition: service_healthy') == 2

def test_no_public_database_or_ollama_port():
    data = content('docker-compose.day23.yml')
    assert '5433:5432' not in data and '11434:11434' not in data
    assert '127.0.0.1:8000:8000' in data

def test_secrets_required():
    data = content('docker-compose.day23.yml')
    assert 'POSTGRES_PASSWORD:?' in data
    assert 'SUPPORTPILOT_JWT_SECRET:?' in data

def test_dockerfile_non_root():
    data = content('Dockerfile')
    assert 'USER supportpilot' in data
    assert 'app.day22_api:app' in data

def test_healthchecks_present():
    data = content('docker-compose.day23.yml')
    assert data.count('healthcheck:') == 3

def test_dockerignore_protects_secrets():
    data = content('.dockerignore').splitlines()
    assert '.env' in data and '.venv' in data and 'artifacts' in data

def test_database_init_present():
    data = content('docker-compose.day23.yml')
    assert './db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro' in data
