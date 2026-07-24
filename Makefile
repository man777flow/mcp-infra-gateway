COMPOSE = docker compose -f docker-compose.generated.yml

.PHONY: install check-config generate deploy update register status health logs stop clean

install: check-config generate deploy register

# The only "setup" step there is: point at the config file. No prompts, ever.
check-config:
	@test -f instances.toml || { \
		echo "instances.toml not found."; \
		echo "  cp instances.toml.example instances.toml"; \
		echo "Edit it: add your Zabbix/Grafana/Nautobot URLs and API keys, then run 'make install' again."; \
		exit 1; \
	}

generate: check-config
	@python3 scripts/generate.py

deploy: generate
	$(COMPOSE) build
	$(COMPOSE) up -d

update: check-config
	@python3 scripts/generate.py
	$(COMPOSE) pull --ignore-buildable
	$(COMPOSE) build --no-cache
	$(COMPOSE) up -d

register:
	@python3 scripts/configure-mcp-clients.py

status:
	$(COMPOSE) ps

health:
	@python3 scripts/health.py

logs:
	$(COMPOSE) logs -f

stop:
	$(COMPOSE) down

clean:
	$(COMPOSE) down -v
	rm -rf generated docker-compose.generated.yml
