# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`desktop-agent` is a dual-purpose project: a working desktop assistant AND an educational reference implementation of every major [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/) concept. Every non-trivial function should include a `# [CONCEPT]` comment explaining which SDK pattern it demonstrates and why.

**Model:** `gpt-4o` (tools + vision). **Package manager:** `uv`.

See `temp/SPEC.md` for the full specification and `temp/CONCEPT.md` for the SDK concept map. These are authoritative — consult them before making architectural decisions.

## Key Commands

```bash
# Run the CLI agent
uv run python -m agent.main

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_tools.py

# Run a single test by name
uv run pytest tests/test_tools.py::test_read_file_returns_content

# Run the web UI (Phase 3)
uv run python -m ui.app

# Install/sync dependencies
uv sync

# Install browser binaries (required for Phase 2)
uv run playwright install chromium
```

## Architecture

Three layers that must stay separated — mixing them is the primary thing to avoid:

| Layer | Location | Role |
|---|---|---|
| **Brain** | `app_agents/` | Agent definitions, system prompts, tool registration |
| **Hands** | `tools/` | Async tool functions — all I/O and side effects live here |
| **Conductor** | `agent/manager.py` | Orchestrates the Runner, owns conversation history |

### Package layout

- `agent/` — Orchestration layer: `manager.py` (AgentManager), `main.py` (CLI loop), `trace.py` (TraceLogger), `approvals.py` (human-in-the-loop gate), `guardrails.py` (@input_guardrail)
- `app_agents/` — Agent definitions: `desktop_agent.py`, `browser_agent.py`, `summary_agent.py`
- `tools/` — Async tool functions: `read.py`, `write.py`, `search.py`, `execute.py`, `browser.py`
- `schemas/models.py` — All Pydantic `BaseModel` return types for tools
- `ui/` — Phase 3 Flask web UI with SSE streaming

> **Important naming:** The local agent definitions directory is `app_agents/`, NOT `agents/`. The name `agents` is reserved by the openai-agents SDK (`from agents import Agent, Runner, trace`). See `findings.md` for details.

### SDK import pattern

```python
from agents import Agent, Runner, trace   # always the SDK
from app_agents.desktop_agent import DesktopAgent  # always our definitions
```

### Control flow

```
User input → @input_guardrail → DesktopAgent (max_turns=15)
    ├── tools/* (async, Pydantic returns)
    ├── SummaryAgent.as_tool()   ← agent-as-tool: parent keeps control
    └── handoff → BrowserAgent  ← handoff: parent exits flow
```

### Two safety layers (keep them separate)

1. `agent/guardrails.py` — SDK `@input_guardrail`, runs **before** the agent sees the message; blocks dangerous patterns at middleware level.
2. `agent/approvals.py` — Application-level `rich` prompt in `run_command`; runs **after** the agent decides to act; requires explicit `y/n` from the user.

## Coding Standards

Full standards live in `.claude/standards.md`, `.claude/python.md`, and `.claude/testing.md`. Critical points:

- **All tools are `async def`** — I/O-bound operations; never make a tool synchronous.
- **All tool return types are Pydantic `BaseModel` subclasses** defined in `schemas/models.py` — never return raw dicts.
- **Docstrings are tool prompts** — the `@function_tool` decorator sends the docstring to the model as the tool description. Treat docstrings as production logic.
- Use `# [CONCEPT]` comments to explain SDK patterns inline — this is an educational codebase.
- `asyncio.gather()` for independent parallel tool calls; sequential `await` when B depends on A.
- `max_turns` must be set explicitly on every agent — never leave it at the default.
