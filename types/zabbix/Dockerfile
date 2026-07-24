ARG BASE_IMAGE=python:3.12-alpine
FROM ${BASE_IMAGE}

RUN apk add --no-cache git \
    && python -m venv /opt/zabbix-mcp/venv \
    && /opt/zabbix-mcp/venv/bin/pip install --no-cache-dir \
       git+https://github.com/initMAX/zabbix-mcp-server.git \
    && adduser -D -u 1000 mcpuser

# config.toml is bind-mounted from the host; the admin portal writes back to it
# on first start. The host file must be writable by uid 1000.
USER mcpuser

EXPOSE 8080 9090

ENTRYPOINT ["/opt/zabbix-mcp/venv/bin/zabbix-mcp-server"]
CMD ["--config", "/etc/zabbix-mcp/config.toml"]
