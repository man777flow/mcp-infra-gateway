FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.5.21 /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 -s /bin/bash mcpuser

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TOKENIZERS_PARALLELISM=false

# utils/path.py walks up from __file__ looking for a parent directory named
# exactly "nautobot_mcp" to locate the ChromaDB path — it must live here, not
# at a bare /app, or the server crashes at import time.
WORKDIR /app/nautobot_mcp

RUN git clone --depth 1 https://github.com/kvncampos/nautobot_mcp.git . \
    && uv sync --locked \
    && mkdir -p backend/chroma_db backend/models \
    && chown -R mcpuser:mcpuser /app

ENV PATH="/app/nautobot_mcp/.venv/bin:$PATH"

USER mcpuser

EXPOSE 8081

ENTRYPOINT ["python", "main.py"]
CMD ["--mode", "stdio"]
