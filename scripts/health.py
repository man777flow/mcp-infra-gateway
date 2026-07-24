#!/usr/bin/env python3
"""Checks health of every instance in generated/registry.json."""
import os
import subprocess
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import REPO_ROOT, load_registry  # noqa: E402


def check_http(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.status < 400
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return False


def check_compose_healthy(container_name):
    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose.generated.yml", "ps", container_name],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return "(healthy)" in result.stdout


def main():
    registry = load_registry()
    if not registry:
        print("No instances in generated/registry.json.")
        return 0

    ok = True
    for entry in registry:
        label = f"{entry['type']} ({entry['name']})"
        if entry["health_kind"] == "http":
            healthy = check_http(entry["health_url"])
        else:
            healthy = check_compose_healthy(entry["container_name"])
        status = "OK" if healthy else "FAIL"
        if not healthy:
            ok = False
        print(f"{label:<30} {status}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
