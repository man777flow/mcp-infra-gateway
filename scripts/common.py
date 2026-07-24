"""Shared helpers for scripts/generate.py, health.py, configure-mcp-clients.py."""
import json
import os
import re

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCES_TOML = os.path.join(REPO_ROOT, "instances.toml")
GENERATED_DIR = os.path.join(REPO_ROOT, "generated")
REGISTRY_PATH = os.path.join(GENERATED_DIR, "registry.json")
COMPOSE_PATH = os.path.join(REPO_ROOT, "docker-compose.generated.yml")


def load_toml(path):
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_registry():
    if not os.path.exists(REGISTRY_PATH):
        raise SystemExit(
            "generated/registry.json not found — run 'make generate' (or 'make deploy') first."
        )
    with open(REGISTRY_PATH) as f:
        return json.load(f)


def render_template(text, mapping):
    """Replace {{VAR}} placeholders; leaves unmatched ones as-is."""

    def repl(m):
        return str(mapping.get(m.group(1), m.group(0)))

    return re.sub(r"\{\{([A-Z0-9_]+)\}\}", repl, text)
