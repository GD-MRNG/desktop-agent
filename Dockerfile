# Multi-stage build: dependency resolution happens in `builder`, the runtime
# image only ever contains the built venv + source, not uv or the lockfile.
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app
COPY pyproject.toml uv.lock ./
# --no-dev skips pytest/pytest-asyncio; --frozen refuses to silently update the lock.
# Playwright is left uninstalled at the browser-binary level (see README) since
# browser_agent.py isn't implemented yet — installing Chromium here would be dead weight.
RUN uv sync --frozen --no-dev

COPY agent/ agent/
COPY app_agents/ app_agents/
COPY tools/ tools/
COPY schemas/ schemas/

FROM python:3.11-slim

RUN useradd --create-home --shell /bin/bash appuser
# Source lives here; the agent's actual working directory (what it reads/writes/
# executes against) is the separate /workspace bind mount, not this path.
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/agent /app/agent
COPY --from=builder /app/app_agents /app/app_agents
COPY --from=builder /app/tools /app/tools
COPY --from=builder /app/schemas /app/schemas

ENV PATH="/app/.venv/bin:$PATH"
# Container-side mount point for the host directory the agent operates on.
# Paired with AGENT_WORKDIR so tool sandboxing is contained to this mount
# regardless of the process's own cwd (which stays /app, where the source lives).
ENV AGENT_WORKDIR=/workspace
RUN mkdir -p /workspace && chown appuser:appuser /workspace

USER appuser

# Requires an interactive TTY + stdin — the human-in-the-loop approval gate in
# agent/approvals.py blocks on stdin before running any shell command.
ENTRYPOINT ["python", "-m", "agent.main"]
