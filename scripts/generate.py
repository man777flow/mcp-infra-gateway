#!/usr/bin/env python3
"""Reads instances.toml and writes docker-compose.generated.yml (as JSON —
valid YAML, avoids a PyYAML dependency and string-templating indentation
bugs) plus generated/registry.json (the single source of truth consumed by
health.py and configure-mcp-clients.py) and each Zabbix instance's
config.toml. Safe to re-run any time instances.toml changes.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (  # noqa: E402
    COMPOSE_PATH,
    GENERATED_DIR,
    INSTANCES_TOML,
    REGISTRY_PATH,
    REPO_ROOT,
    keychain_get,
    load_toml,
    render_template,
)

REQUIRED_FIELDS = {
    "zabbix": ["name", "url", "api_token_keychain", "port", "admin_port"],
    "grafana": ["name", "url", "api_token_keychain", "port"],
    "nautobot": ["name", "url", "api_token_keychain", "port"],
}


def fail(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_instances():
    if not os.path.exists(INSTANCES_TOML):
        fail(
            "instances.toml not found.\n"
            "  cp instances.toml.example instances.toml\n"
            "Edit it: add your Zabbix/Grafana/Nautobot URLs and API keys, then re-run."
        )
    data = load_toml(INSTANCES_TOML)
    for kind in ("zabbix", "grafana", "nautobot"):
        data.setdefault(kind, [])
    return data


def validate(data):
    seen_names = set()
    seen_ports = {}

    def check_port(port, where):
        if port in seen_ports:
            fail(f"port {port} used by both {seen_ports[port]} and {where} — ports must be unique")
        seen_ports[port] = where

    for kind, entries in data.items():
        if kind not in REQUIRED_FIELDS:
            continue
        for entry in entries:
            for field in REQUIRED_FIELDS[kind]:
                if field not in entry:
                    fail(f"[[{kind}]] entry {entry.get('name', '?')!r} is missing required field '{field}'")
            key = (kind, entry["name"])
            if key in seen_names:
                fail(f"duplicate {kind} instance name '{entry['name']}' — names must be unique per type")
            seen_names.add(key)
            check_port(entry["port"], f"{kind}.{entry['name']}")
            if kind == "zabbix":
                check_port(entry["admin_port"], f"{kind}.{entry['name']} (admin_port)")


def zabbix_service(entry):
    name = entry["name"]
    outdir = os.path.join(GENERATED_DIR, f"zabbix-{name}")
    os.makedirs(outdir, exist_ok=True)
    template_path = os.path.join(REPO_ROOT, "types", "zabbix", "config.toml.template")
    with open(template_path) as f:
        template = f.read()
    rendered = render_template(
        template,
        {
            "NAME": name,
            "URL": entry["url"],
            "API_TOKEN": keychain_get(entry["api_token_keychain"]),
            "READ_ONLY": str(entry.get("read_only", False)).lower(),
            "VERIFY_SSL": str(entry.get("verify_ssl", True)).lower(),
        },
    )
    config_path = os.path.join(outdir, "config.toml")
    with open(config_path, "w") as f:
        f.write(rendered)
    os.chmod(config_path, 0o600)

    container_name = f"zabbix-mcp-{name}"
    service = {
        "build": {"context": "types/zabbix", "dockerfile": "Dockerfile"},
        "container_name": container_name,
        "restart": "unless-stopped",
        "ports": [
            f"{entry['port']}:8080",
            f"{entry['admin_port']}:9090",
        ],
        "volumes": [f"./generated/zabbix-{name}/config.toml:/etc/zabbix-mcp/config.toml"],
        "networks": ["mcp-net"],
        "healthcheck": {
            "test": [
                "CMD",
                "python",
                "-c",
                "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')",
            ],
            "interval": "30s",
            "timeout": "5s",
            "retries": 3,
        },
    }
    registry_entry = {
        "type": "zabbix",
        "name": name,
        "container_name": container_name,
        "port": entry["port"],
        "admin_port": entry["admin_port"],
        "mcp_url": f"http://localhost:{entry['port']}/mcp",
        "health_kind": "http",
        "health_url": f"http://localhost:{entry['port']}/health",
    }
    return container_name, service, registry_entry


def grafana_service(entry):
    name = entry["name"]
    port = entry["port"]
    container_name = f"grafana-mcp-{name}"
    service = {
        "image": "grafana/mcp-grafana:latest",
        "container_name": container_name,
        "restart": "unless-stopped",
        "network_mode": "host",
        "environment": {
            "GRAFANA_URL": entry["url"],
            "GRAFANA_SERVICE_ACCOUNT_TOKEN": keychain_get(entry["api_token_keychain"]),
        },
        "command": ["-transport", "streamable-http", "-address", f"0.0.0.0:{port}"],
        "healthcheck": {
            "test": [
                "CMD",
                "perl",
                "-MIO::Socket",
                "-e",
                f'$$s=IO::Socket::INET->new(\'localhost:{port}\'); print $$s "GET /healthz HTTP/1.0\\r\\n\\r\\n"; while(<$$s>){{exit 0 if /200 OK/}} exit 1',
            ],
            "interval": "30s",
            "timeout": "5s",
            "retries": 3,
        },
    }
    registry_entry = {
        "type": "grafana",
        "name": name,
        "container_name": container_name,
        "port": port,
        "mcp_url": f"http://localhost:{port}/mcp",
        "health_kind": "http",
        "health_url": f"http://localhost:{port}/healthz",
    }
    return container_name, service, registry_entry


def nautobot_service(entry):
    name = entry["name"]
    port = entry["port"]
    container_name = f"nautobot-mcp-{name}"
    service = {
        "build": {"context": "types/nautobot", "dockerfile": "Dockerfile"},
        "container_name": container_name,
        "restart": "unless-stopped",
        "network_mode": "host",
        "environment": {
            "NAUTOBOT_ENV": "prod",
            "NAUTOBOT_PROD_BASE_URL": entry["url"],
            "NAUTOBOT_PROD_TOKEN": keychain_get(entry["api_token_keychain"]),
            "NAUTOBOT_TOKEN": keychain_get(entry["api_token_keychain"]),
            "GITHUB_TOKEN": keychain_get(entry["github_token_keychain"])
            if entry.get("github_token_keychain")
            else "",
            "SSL_VERIFY": "true",
            "MCP_TRANSPORT": "http",
            "MCP_PORT": str(port),
        },
        "command": ["--mode", "http", "--port", str(port)],
        "volumes": [
            f"nautobot-{name}-chroma:/app/nautobot_mcp/backend/chroma_db",
            f"nautobot-{name}-models:/app/nautobot_mcp/backend/models",
        ],
        "healthcheck": {
            "test": [
                "CMD",
                "python",
                "-c",
                f"import socket; socket.create_connection(('127.0.0.1', {port}), timeout=3).close()",
            ],
            "interval": "30s",
            "timeout": "5s",
            "retries": 3,
        },
    }
    registry_entry = {
        "type": "nautobot",
        "name": name,
        "container_name": container_name,
        "port": port,
        "mcp_url": f"http://localhost:{port}/mcp/",
        "health_kind": "compose",
        "health_url": None,
    }
    volumes = {f"nautobot-{name}-chroma": {}, f"nautobot-{name}-models": {}}
    return container_name, service, registry_entry, volumes


def main():
    data = load_instances()
    validate(data)

    os.makedirs(GENERATED_DIR, exist_ok=True)

    services = {}
    registry = []
    volumes = {}

    for entry in data["zabbix"]:
        _, service, reg = zabbix_service(entry)
        services[reg["container_name"]] = service
        registry.append(reg)

    for entry in data["grafana"]:
        _, service, reg = grafana_service(entry)
        services[reg["container_name"]] = service
        registry.append(reg)

    for entry in data["nautobot"]:
        _, service, reg, vols = nautobot_service(entry)
        services[reg["container_name"]] = service
        registry.append(reg)
        volumes.update(vols)

    compose = {"services": services}
    if any(reg["type"] == "zabbix" for reg in registry):
        compose["networks"] = {"mcp-net": {"driver": "bridge"}}
    if volumes:
        compose["volumes"] = volumes

    with open(COMPOSE_PATH, "w") as f:
        json.dump(compose, f, indent=2)
        f.write("\n")
    os.chmod(COMPOSE_PATH, 0o600)

    with open(REGISTRY_PATH, "w") as f:
        json.dump(registry, f, indent=2)
        f.write("\n")

    print(f"Generated {len(registry)} instance(s):")
    for reg in registry:
        extra = f" (admin: :{reg['admin_port']})" if reg["type"] == "zabbix" else ""
        print(f"  {reg['type']:<9} {reg['name']:<15} {reg['mcp_url']}{extra}")


if __name__ == "__main__":
    main()
