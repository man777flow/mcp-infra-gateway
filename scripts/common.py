"""Shared helpers for scripts/generate.py, health.py, configure-mcp-clients.py."""
import json
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTANCES_TOML = os.path.join(REPO_ROOT, "instances.toml")
GENERATED_DIR = os.path.join(REPO_ROOT, "generated")
REGISTRY_PATH = os.path.join(GENERATED_DIR, "registry.json")
COMPOSE_PATH = os.path.join(REPO_ROOT, "docker-compose.generated.yml")

# k9 fork: secrets live in macOS Keychain (~/.claude/scripts/secret.sh), never
# in instances.toml — see instances.toml.example.
SECRET_SH = os.path.expanduser("~/.claude/scripts/secret.sh")


def keychain_get(name):
    """Resolve a Keychain secret name to its value via secret.sh get."""
    result = subprocess.run(
        ["sh", SECRET_SH, "get", name], capture_output=True, text=True
    )
    if result.returncode != 0:
        print(
            f"error: Keychain secret '{name}' not found. "
            f"Set it with: printf %s \"<token>\" | sh {SECRET_SH} set {name}",
            file=sys.stderr,
        )
        sys.exit(1)
    return result.stdout.rstrip("\n")


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
