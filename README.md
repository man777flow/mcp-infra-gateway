# mcp-infra-gateway

A generic, multi-instance MCP gateway for Zabbix, Grafana, and Nautobot. Bring
your own servers — as many of each as you need — and expose them to any
MCP-capable AI client (Claude Code, VSCode, Cursor, Antigravity) with one
config file and one command.

This repo is **deployment-only**: no application code lives here. Each MCP
server implementation is pulled from its upstream project at build time;
this repo wires them up and runs one container per server instance you
declare. Not tied to any one organization's infrastructure.

## Why one container per instance

Zabbix, Grafana, and Nautobot are each accessed through a small MCP server
process. Some of those upstream projects can juggle multiple backends from
one running process; some can't. Rather than special-case that, every
instance here — one Zabbix, five Zabbixes, three Grafanas, whatever — gets
its own container, its own port, and its own name. Simple, consistent,
scales to any number.

## Quick start

```bash
git clone https://github.com/washosk/mcp-infra-gateway.git
cd mcp-infra-gateway
cp instances.toml.example instances.toml
```

Edit `instances.toml`: for each Zabbix/Grafana/Nautobot server you want
access to, add a block with its URL, an API key, and a port. See the
comments in the example file — a couple of entries are filled in as a
template, the rest are commented out.

```bash
make install
```

That builds and starts one container per instance you declared, then
registers each one with whatever AI client it finds on your machine.
**Nothing is prompted for interactively** — if you run `make install` before
editing `instances.toml`, it just tells you to copy the example and fill it
in, then exits.

## Getting API keys

- **Zabbix**: log in → Administration → API tokens → Create API token.
- **Grafana**: log in → Administration → Service accounts → Add service
  account → Add token.
- **Nautobot**: log in → your profile → API tokens.

`instances.toml` holds these in plain text and is gitignored — it never
leaves your machine and is never committed.

## Example: multi-tenant configuration

`instances.toml.example` covers the single-instance case. For a fuller
picture of what multi-tenancy looks like in practice —
[`examples/multi-tenant.instances.toml`](examples/multi-tenant.instances.toml)
is a mock setup for an ops team running its own infrastructure plus
monitoring for two separate client organizations:

```toml
[[zabbix]]
name = "acme-prod"
url = "https://zabbix.acme-ops.example.com"
api_token = "..."
port = 8001
admin_port = 9001

[[zabbix]]
name = "client-a-prod"
url = "https://zabbix.client-a.example.com"
api_token = "..."
port = 8002
admin_port = 9002
read_only = true          # this team only monitors client-a, doesn't manage it

# ...plus client-b-staging, two Grafana instances, one Nautobot instance —
# see the full file for all six.
```

Every value in that file is mock data — copy it as a starting point
(`cp examples/multi-tenant.instances.toml instances.toml`), then replace
each `url`/`api_token` with your real ones and pick ports that are free on
your machine. Each instance still gets its own container, named
`<type>-<name>` — `zabbix-acme-prod`, `zabbix-client-a-prod`,
`grafana-client-a-prod`, and so on.

## Makefile reference

```bash
make install    # first time: check config, generate, build, start, register
make generate   # regenerate docker-compose.generated.yml from instances.toml
make deploy     # generate + build + start (no client registration)
make update     # pull/rebuild latest images and restart
make register   # (re-)register every instance with detected AI clients
make status     # docker compose ps
make health     # check every instance's health
make logs       # follow container logs
make stop       # stop the stack
make clean      # stop, remove volumes, delete generated files
```

Run `make generate` (or `make deploy`/`make install`) again any time you add,
remove, or edit an entry in `instances.toml` — it's idempotent and safe to
re-run.

Nautobot instances take several minutes to report healthy on first start
(they index the live API schema and clone a large reference repo for
knowledge-base search) — `docker compose ps` shows `unhealthy` the whole
time, that's expected. See [`types/nautobot/README.md`](types/nautobot/README.md).

## How it works

```
instances.toml              # you edit this: URLs + API keys, one block per instance
        │
        ▼  scripts/generate.py
        │
docker-compose.generated.yml   # one service per instance (gitignored, regenerated)
generated/registry.json        # {type, name, port, mcp_url, ...} per instance
generated/zabbix-<name>/config.toml   # per-instance Zabbix MCP config
```

`scripts/generate.py` validates `instances.toml` (no duplicate names or
ports across all instances), then builds the compose file and, for Zabbix
instances, that instance's `config.toml`. `scripts/health.py` and
`scripts/configure-mcp-clients.py` both drive themselves from
`generated/registry.json` — adding a new instance to `instances.toml` is the
only thing you ever need to touch.

Each server *type* (`types/zabbix/`, `types/grafana/`, `types/nautobot/`)
holds its Dockerfile (if built from source) and its config template — see
each type's own README for upstream quirks and workarounds.

## Registered MCP server names

Each instance registers as `<type>-<name>` — e.g. an entry named `prod`
under `[[zabbix]]` becomes `zabbix-prod`. Run `make register`, or see
[CLIENTS.md](CLIENTS.md) for manual per-client setup.

## Repository layout

```
Makefile
instances.toml.example        # committed template
examples/                     # committed, fuller mock example (multi-tenant)
instances.toml                # gitignored — your real URLs + API keys
docker-compose.generated.yml  # gitignored — generated
generated/                    # gitignored — generated per-instance config + registry
scripts/
  common.py                    # shared helpers (load instances.toml / registry.json)
  generate.py                  # instances.toml -> compose + per-instance config + registry
  configure-mcp-clients.py     # registers every instance with detected AI clients
  health.py                    # checks every instance's health
types/
  zabbix/    Dockerfile, config.toml.template, README.md
  grafana/   README.md (official image, no build)
  nautobot/  Dockerfile, README.md
CLIENTS.md
LICENSE
```

## Troubleshooting

```bash
make status                              # are the containers up?
make health                              # is each instance responding?
make logs                                # what are they saying?
docker compose -f docker-compose.generated.yml logs <container-name>
```

If a Zabbix instance's admin portal (`http://localhost:<admin_port>`) has no
working login yet, that's expected — no admin password is pre-generated; set
one on first visit. See [`types/zabbix/README.md`](types/zabbix/README.md).

## License

MIT — see [LICENSE](LICENSE).
