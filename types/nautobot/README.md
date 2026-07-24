# Nautobot MCP type

Source: [`github.com/kvncampos/nautobot_mcp`](https://github.com/kvncampos/nautobot_mcp), `git clone`d at build time in `Dockerfile`.

- All Nautobot instances declared in `instances.toml` share this one built
  image; `scripts/generate.py` runs one container per instance, each bound to
  its own port via `network_mode: host` (see below) and its own env vars.
- Every generated container is always wired into upstream's `prod` env slot
  (`NAUTOBOT_PROD_BASE_URL`/`NAUTOBOT_PROD_TOKEN`) regardless of the
  instance's name in `instances.toml` — since each container only ever talks
  to one Nautobot, there's no need to use upstream's `local`/`nonprod`/`prod`
  distinction for anything.
- **Needs a custom Dockerfile, not the upstream one** — upstream's own
  `Dockerfile` does `COPY . /app`, but `utils/path.py` walks up from
  `__file__` looking for a parent directory literally named `nautobot_mcp` to
  locate the ChromaDB path. Under `/app` that directory never exists, so the
  container crash-loops at import time. This `Dockerfile` clones into
  `/app/nautobot_mcp` instead.
- **`network_mode: host`, not a published port** — `main.py`'s
  `run_http_mode()` calls FastMCP's `run_async(transport="streamable-http",
  port=port)` with no `host` argument, so it always binds `127.0.0.1`
  regardless of the configured port. A bridge-network port mapping can never
  reach a loopback-only bind — sharing the host netns makes each instance's
  chosen port reachable as `localhost:<port>`. Multiple host-networked
  containers coexist fine as long as each uses a distinct port, which
  `scripts/generate.py` enforces.
- **`path` argument to `nautobot_dynamic_api_request` excludes `/api`** — the
  configured base URL already includes it; use `path: "/status/"` for
  `GET /api/status/`, not `path: "/api/status/"`.
- **No HTTP health endpoint** — the container healthcheck is a bare TCP
  probe; `scripts/health.py` checks `docker compose ps` health status
  instead of curling an endpoint for this type.
- **First start takes several minutes** — it indexes the live Nautobot
  OpenAPI schema and clones `nautobot/nautobot` (~180MB) for
  knowledge-base search, into an unmounted path, so this repeats on every
  restart. `docker compose ps` shows `unhealthy` for the whole stretch since
  the HTTP listener doesn't start until it's done. Normal, not a hang —
  watch `docker compose logs -f <container-name>`.
