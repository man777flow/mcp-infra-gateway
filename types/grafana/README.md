# Grafana MCP type

Source: official [`grafana/mcp-grafana`](https://hub.docker.com/r/grafana/mcp-grafana) image — no local build, no Dockerfile in this folder.

- All Grafana instances declared in `instances.toml` share this one image;
  `scripts/generate.py` runs one container per instance, each with its own
  `GRAFANA_URL`/`GRAFANA_SERVICE_ACCOUNT_TOKEN` env vars and its own port.
- **`network_mode: host`** — the upstream binary's `/healthz` always binds
  `127.0.0.1` regardless of `-address`, so a bridge-network port mapping
  can never reach it. Sharing the host netns makes each instance's chosen
  port reachable as `localhost:<port>`. Multiple host-networked containers
  coexist fine as long as each uses a distinct port, which
  `scripts/generate.py` enforces.
