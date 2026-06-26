# desktop-agent

## Description

Built to augment a developer's day-to-day coding work — reading and writing files,
searching the codebase, running commands, and looking up documentation — without
switching context out of the terminal. The agent is a less expensive frontier model
connected to a set of tools via the OpenAI Agents SDK scaffold.

Every shell command requires explicit approval before it runs. Tools are separated from
agent reasoning by design so either side can be swapped independently. The agent
enforces a safety guardrail before it reasons, and a human-in-the-loop gate before it
acts.

## What this demonstrates

This repo is a reference implementation of core agentic engineering patterns using the
OpenAI Agents SDK. The application is a working tool, but the primary purpose is to make
these patterns visible and understandable:

- **Tool-calling agent loop** — a reasoning agent that selects and calls tools across
  multiple turns to complete multi-step tasks
- **Dual safety layers** — SDK middleware guardrail (fires before reasoning) and a
  human-in-the-loop approval gate (fires before action) as two intentionally separate
  safety concerns
- **Model routing by cost/capability** — cheap `gpt-4o-mini` for the fast safety check,
  expensive `gpt-4o` only for reasoning; the same pattern as routing between Claude and
  Gemini by task type
- **Async concurrent tool execution** — `asyncio.gather()` to run independent tools in
  parallel without blocking
- **Agent-as-tool composition** — a sub-agent (`SummaryAgent`) registered as a callable
  tool so the parent agent retains control, contrasted with a `handoff` where it does not
- **LLM-as-judge evaluation** — 18 E2E test scenarios rated PASS / PARTIAL / FAIL by a
  separate model, the standard approach for evaluating non-deterministic agent outputs

### Why OpenAI Agents SDK, and how it maps to LangChain

The SDK sits close to raw API calls, which keeps the patterns visible. The same concepts
appear in LangChain under different names:

| OpenAI Agents SDK | LangChain equivalent |
|---|---|
| `@function_tool` | `Tool` / `StructuredTool` |
| `Agent` + `Runner` | `AgentExecutor` / LCEL agent chain |
| `handoff` | Conditional edge / Router in LangGraph |
| `@input_guardrail` | `RunnableLambda` input validator |

The model is also swappable — replacing `gpt-4o` with `claude-sonnet-4-5` or
`gemini-2.0-flash` requires no structural changes.

## Capabilities

When working well, the agent can handle these tasks in a single conversation:

### Files

- Read any file and return its contents
- List the contents of a directory
- Write a new file or overwrite an existing one
- Append to a file without touching existing content
- Search recursively across the codebase by keyword, with line numbers

### Web

- Search the web via DuckDuckGo for current information not in training data

### Code execution

The agent can run any shell command — PowerShell on Windows, Bash on Unix.

Before anything runs, an explicit approval prompt appears:

```
⚠ APPROVAL REQUIRED
  Command : echo hello world
  Cwd     : .
  Allow? [y/N]:
```

Approve with `y`. Deny with `n` or Enter. The agent never retries a denied command.
After approval, stdout and stderr are captured and returned, along with the exit code.
Useful for running test suites, build commands, git operations, or one-off scripts
alongside a coding session.

### Documentation lookup

- Resolve any library or framework to a canonical ID, then fetch live documentation
  and code examples via the Context7 MCP server
- Avoids stale training-data answers for libraries that change frequently

### Summarisation

- Condense any text into 3–5 sentences via a nested summarisation sub-agent

### Safety

- An input guardrail intercepts dangerous patterns (destructive commands, SQL drops,
  disk formatting) before the agent reasons
- The shell approval gate gives the user final veto over every command the agent wants
  to run

## Setup

### Prerequisites

**uv** — install from [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/)
before anything else. The project uses uv for dependency management and running scripts.

**OpenAI API key** — the agent runs on `gpt-4o`. Create a `.env` file at the project root:

```
OPENAI_API_KEY=sk-...
```

Get a key from [platform.openai.com](https://platform.openai.com/api-keys).

**Context7 API key** (optional) — set `CONTEXT7_API_KEY=...` in `.env` for a higher
rate limit on documentation lookups. The free tier works without one.

### Install & configure

```bash
# Clone and enter the project
git clone <repo-url>
cd desktop-agent

# Install dependencies
uv sync
```

### Usage

```bash
# Start the CLI agent
uv run python -m agent.main
```

Type `exit` or `quit` to stop. The agent maintains conversation history within a session.

### Tests

```bash
# Run all unit tests
uv run pytest

# Run a single test file
uv run pytest tests/test_tools.py

# Run a single test by name
uv run pytest tests/test_tools.py::test_read_file_returns_content

# Run the end-to-end evaluation suite (requires OPENAI_API_KEY)
uv run python agent/evaluate.py
```

## Evaluation

The E2E test catalogue in [`docs/e2e.md`](docs/e2e.md) covers 18 scenarios across
every capability group. The evaluation runner drives the agent through each test
programmatically and uses an **LLM-as-judge pattern** (`gpt-4o-mini` as evaluator) to
rate results PASS / PARTIAL / FAIL. This is the standard approach for evaluating
non-deterministic agent outputs at scale — a deterministic assert cannot tell you
whether an agent's reasoning was correct.

See [`docs/evaluation.md`](docs/evaluation.md) for the evaluation approach and a log
of past runs.

## Key files for a technical reviewer

| File | What it demonstrates |
|---|---|
| `app_agents/desktop_agent.py` | Agent composition, CoT system prompt, docstring-as-tool-prompt, agent-as-tool |
| `agent/guardrails.py` | `@input_guardrail` SDK middleware, model routing by cost/capability |
| `agent/approvals.py` | Human-in-the-loop approval gate (application-level, post-reasoning) |
| `agent/manager.py` | Conductor pattern — Runner orchestration, conversation history ownership |
| `tools/search.py` | `asyncio.gather()` concurrent tool execution |
| `agent/evaluate.py` | LLM-as-judge evaluation runner, `CapturingLogger` mock for tool call inspection |
