#!/usr/bin/env python3
"""Registers every instance in generated/registry.json with detected AI
clients (Claude Code, VSCode, Cursor, Antigravity)."""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import load_registry  # noqa: E402


def confirm(prompt):
    try:
        answer = input(f"{prompt} [y/N]: ").strip().lower()
    except EOFError:
        answer = ""
    return answer in ("y", "yes")


def server_id(entry):
    return f"{entry['type']}-{entry['name']}"


def write_json_config(path, key, registry):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    servers = {server_id(e): {"type": "http", "url": e["mcp_url"]} for e in registry}
    with open(path, "w") as f:
        json.dump({key: servers}, f, indent=2)
        f.write("\n")


def main():
    registry = load_registry()
    if not registry:
        print("No instances in generated/registry.json — nothing to register.")
        return 1

    names = ", ".join(server_id(e) for e in registry)
    found = 0

    if subprocess.run(["which", "claude"], capture_output=True).returncode == 0:
        found += 1
        print("[FOUND] Claude Code CLI")
        if confirm(f"Register {names} with Claude Code?"):
            for e in registry:
                subprocess.run(
                    ["claude", "mcp", "add", "-s", "user", server_id(e), "--transport", "http", e["mcp_url"]],
                    check=False,
                )
            print("Claude Code configured.")

    home = os.path.expanduser("~")

    vscode_dir = os.path.join(home, ".config", "Code")
    if os.path.isdir(vscode_dir):
        found += 1
        print("[FOUND] VSCode")
        vscode_config = os.path.join(vscode_dir, "User", "mcp.json")
        if confirm(f"Create/Update VSCode MCP configuration ({vscode_config})?"):
            write_json_config(vscode_config, "servers", registry)
            print("VSCode configuration updated.")

    cursor_dir = os.path.join(home, ".cursor")
    if os.path.isdir(cursor_dir):
        found += 1
        print("[FOUND] Cursor")
        cursor_config = os.path.join(cursor_dir, "mcp.json")
        if confirm(f"Create/Update Cursor MCP configuration ({cursor_config})?"):
            write_json_config(cursor_config, "mcpServers", registry)
            print("Cursor configuration updated.")

    antigravity_dir = os.path.join(home, ".antigravity")
    if os.path.isdir(antigravity_dir):
        found += 1
        print("[FOUND] Antigravity")
        antigravity_config = os.path.join(antigravity_dir, "mcp.json")
        if confirm(f"Create/Update Antigravity MCP configuration ({antigravity_config})?"):
            write_json_config(antigravity_config, "mcpServers", registry)
            print("Antigravity configuration updated.")

    if found == 0:
        print("\nNo common MCP clients (Claude Code, VSCode, Cursor, Antigravity) detected.")
        print("Install one, then re-run this script to register the instances.")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
