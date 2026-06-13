# desktop-agent

A working desktop assistant built with the OpenAI Agents SDK

## Capabilities

### File system
- Read files and list directory contents
- Write and append to files
- Recursive text search across files with line-number results

### Clipboard
- Read from and write to the system clipboard

### Web search
- Search the web via DuckDuckGo for current information

### Shell execution
- Run shell commands (PowerShell on Windows, Bash on Unix)
- Every command requires explicit user approval before it runs

### Summarisation
- Condense text via a nested summary sub-agent

### Documentation lookup (Context7)
- Resolve any library or framework name to a canonical ID
- Fetch live, up-to-date documentation and code examples via the Context7 MCP server
- Set `CONTEXT7_API_KEY` in `.env` for a higher rate limit (free tier works without one)

### Safety
- Input guardrail blocks dangerous patterns before the agent reasons
- Human-in-the-loop approval gate for all shell commands

---

> **Demo results** — coming soon

---

## Prerequisites

**uv** — this project uses [uv](https://docs.astral.sh/uv/getting-started/installation/) for dependency management and running scripts. Install it before anything else.

**OpenAI API key** — the agent runs on `gpt-4o` and requires a valid key. Create a `.env` file at the project root:

```
OPENAI_API_KEY=sk-...
```

You can get a key from [platform.openai.com](https://platform.openai.com/api-keys). Without it the agent will fail to start.

## Usage

```bash
# Install dependencies
uv sync

# Run the CLI agent
uv run python -m agent.main
```

## Tests

```bash
# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_tools.py

# Run a single test by name
uv run pytest tests/test_tools.py::test_read_file_returns_content
```