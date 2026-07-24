# Zabbix MCP type

Source: [`github.com/initMAX/zabbix-mcp-server`](https://github.com/initMAX/zabbix-mcp-server), built from source in `Dockerfile`.

- All Zabbix instances declared in `instances.toml` share this one built
  image — `scripts/generate.py` just runs one container per instance, each
  with its own bind-mounted `config.toml` (generated from
  `config.toml.template`) and its own port pair (`port` for the MCP
  endpoint, `admin_port` for the per-instance admin portal).
- **Admin portal credentials aren't pre-seeded.** The generated
  `config.toml` intentionally omits `[admin.users.admin]` — log in to that
  instance's admin portal (`http://localhost:<admin_port>`) on first access
  to set one, per upstream's own convention, rather than this repo
  generating and printing a password (which would need `werkzeug` installed
  to produce a valid hash).
- **`config.toml` must be writable by uid 1000** — the container runs as
  `mcpuser` (uid 1000), since the admin portal writes changes back to it.
  On a typical single-user Linux desktop your user already is uid 1000.
- Note: `zabbix-mcp-server` itself natively supports *multiple* named
  `[zabbix.<name>]` blocks in one `config.toml`, with tool calls taking a
  `server` parameter to pick one. This repo doesn't use that — it runs one
  container per instance instead, for consistency with Grafana and Nautobot
  (whose upstream images are strictly single-endpoint-per-process). If you'd
  rather run fewer containers, you can hand-edit a generated `config.toml` to
  add more `[zabbix.<name>]` blocks yourself; `make generate` will overwrite
  that the next time it runs, though.
