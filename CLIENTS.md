# MCP Client Setup

Instances must be running first (`make deploy` or `make install`).

Transport: **streamable-http**. Each instance's endpoint is
`http://localhost:<port>/mcp` (Nautobot: `http://localhost:<port>/mcp/`,
trailing slash — `/mcp` 307-redirects to it).

`make register` (or `python3 scripts/configure-mcp-clients.py`) does the
below automatically for any client it detects, for every instance declared
in `instances.toml`. The examples below use the sample entries from
`instances.toml.example` (`zabbix`/`grafana`/`nautobot`, all named `prod`) —
substitute your own instance names and ports.

---

## Claude Code

```bash
claude mcp add -s user zabbix-prod --transport http http://localhost:8001/mcp
claude mcp add -s user grafana-prod --transport http http://localhost:8101/mcp
claude mcp add -s user nautobot-prod --transport http http://localhost:8201/mcp/

# Verify
claude mcp list
```

---

## VSCode

Create `~/.config/Code/User/mcp.json`:

```json
{
  "servers": {
    "zabbix-prod": { "type": "http", "url": "http://localhost:8001/mcp" },
    "grafana-prod": { "type": "http", "url": "http://localhost:8101/mcp" },
    "nautobot-prod": { "type": "http", "url": "http://localhost:8201/mcp/" }
  }
}
```

In VSCode 1.99+: open GitHub Copilot Chat (`Ctrl+Alt+I`), switch to Agent mode.

---

## Cursor / Antigravity

Create `~/.cursor/mcp.json` (or `~/.antigravity/mcp.json`):

```json
{
  "mcpServers": {
    "zabbix-prod": { "type": "http", "url": "http://localhost:8001/mcp" },
    "grafana-prod": { "type": "http", "url": "http://localhost:8101/mcp" },
    "nautobot-prod": { "type": "http", "url": "http://localhost:8201/mcp/" }
  }
}
```

---

## Test the connection

In any client, ask something instance-specific, e.g. `"List 5 hosts from zabbix-prod"`.
If you get a result, MCP is working.

If not:

1. Check containers: `make status`
2. Check health: `make health`
3. Test the endpoint directly:
   ```bash
   curl -X POST http://localhost:<port>/mcp \
     -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}'
   ```
4. Verify the client config file is valid JSON and in the right location.
5. Restart the client.
