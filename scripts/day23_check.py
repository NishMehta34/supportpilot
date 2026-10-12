"""Run on the host after `docker compose -f docker-compose.day23.yml up -d --build`."""
import json
import subprocess
import urllib.request

COMPOSE = ["docker", "compose", "-f", "docker-compose.day23.yml"]

def main():
    status = subprocess.run(COMPOSE + ["ps", "--format", "json"], capture_output=True, text=True, check=True)
    services = {}
    for line in status.stdout.splitlines():
        if line.strip():
            item = json.loads(line)
            services[item["Service"]] = {"state": item.get("State"), "health": item.get("Health", "")}
    with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=10) as response:
        api = json.load(response)
    assert api.get("status") == "ok", api
    assert all(s in services for s in ("api", "db", "ollama")), services
    assert all(services[s]["state"] == "running" for s in ("api", "db", "ollama")), services
    assert all(services[s]["health"] == "healthy" for s in ("api", "db", "ollama")), services
    print("DAY 23 PASSED: 3 healthy containers and HTTP /health")
    print(json.dumps({"services": services, "api": api}, indent=2))

if __name__ == "__main__":
    main()
